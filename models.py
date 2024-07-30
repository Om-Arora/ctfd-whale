import random
import uuid
import hashlib
from datetime import datetime

from jinja2 import Template

from CTFd.utils import get_config
from CTFd.models import db, Flags, Challenges, Users
from CTFd.plugins.dynamic_challenges import DynamicChallenge


class WhaleConfig(db.Model):
    key = db.Column(db.String(length=128), primary_key=True)
    value = db.Column(db.Text)

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return "<WhaleConfig {0} {1}>".format(self.key, self.value)


class WhaleRedirectTemplate(db.Model):
    key = db.Column(db.String(20), primary_key=True)
    frp_template = db.Column(db.Text)
    access_template = db.Column(db.Text)

    def __init__(self, key, access_template, frp_template):
        self.key = key
        self.access_template = access_template
        self.frp_template = frp_template

    def __repr__(self):
        return "<WhaleRedirectTemplate {0}>".format(self.key)


class DynamicDockerChallenge(DynamicChallenge):
    __mapper_args__ = {"polymorphic_identity": "dynamic_docker"}
    id = db.Column(
        db.Integer, db.ForeignKey("dynamic_challenge.id", ondelete="CASCADE"), primary_key=True
    )

    memory_limit = db.Column(db.Text, default="128m")
    cpu_limit = db.Column(db.Float, default=0.5)
    dynamic_score = db.Column(db.Integer, default=0)

    docker_image = db.Column(db.Text, default=0)
    redirect_type = db.Column(db.Text, default=0)
    redirect_port = db.Column(db.Integer, default=0)

    def __init__(self, *args, **kwargs):
        kwargs["initial"] = kwargs["value"]
        super(DynamicDockerChallenge, self).__init__(**kwargs)


class WhaleContainer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(None, db.ForeignKey("users.id"))
    challenge_id = db.Column(None, db.ForeignKey("challenges.id"))
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    renew_count = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.Integer, default=1)
    uuid = db.Column(db.String(256))
    port = db.Column(db.Integer, nullable=True, default=0)
    flag = db.Column(db.String(128), nullable=False)

    # Relationships
    user = db.relationship(
        "Users", foreign_keys="WhaleContainer.user_id", lazy="select"
    )
    challenge = db.relationship(
        "DynamicDockerChallenge", foreign_keys="WhaleContainer.challenge_id", lazy="select"
    )

    @property
    def http_subdomain(self):
        return Template(get_config(
            'whale:template_http_subdomain', '{{ container.uuid }}'
        )).render(container=self)

    def __init__(self, user_id, challenge_id):
        self.user_id = user_id
        self.challenge_id = challenge_id
        self.start_time = datetime.now()
        self.renew_count = 0
        self.uuid = str(uuid.uuid4())

        # THIS DOES NOT CHECK WHETHER FLAG EXISTS ----- THAT IS ASSUMMED!
        all_flags = Flags.query.filter_by(challenge_id=challenge_id)
        existing_flag = all_flags.first()

        user = Users.query.filter_by(id=user_id).first()
        team_id = user.team_id

        # Generate SHA-512 hash of the user ID
        # BETTER TO ADD THIS SALT AS GET_CONFIG!!!!
        hash_content = str(team_id) + str(challenge_id) + " salt for the custom flag feature of n00bzCTF 2024"
        new_flag_content = hashlib.sha512(hash_content.encode()).hexdigest()[58:70] # 12 chars in the middle

        new_flag_content = existing_flag.content.replace('REPLACETHIS', new_flag_content)

        # Add the new flag to the challenge
        new_flag = Flags(
            challenge_id=challenge_id,
            type='static',  # 'static' is one type of flag; other types are 'regex', 'dynamic', etc.
            content=new_flag_content,
            data=''
        )

        if all_flags.filter_by(content=new_flag_content).first() is None:
            db.session.add(new_flag)
            db.session.commit()

        self.flag = Template(new_flag_content).render(container=self, uuid=uuid, random=random, get_config=get_config)


    @property
    def user_access(self):
        return Template(WhaleRedirectTemplate.query.filter_by(
            key=self.challenge.redirect_type
        ).first().access_template).render(container=self, get_config=get_config)

    @property
    def frp_config(self):
        return Template(WhaleRedirectTemplate.query.filter_by(
            key=self.challenge.redirect_type
        ).first().frp_template).render(container=self, get_config=get_config)

    def __repr__(self):
        return "<WhaleContainer ID:{0} {1} {2} {3} {4}>".format(self.id, self.user_id, self.challenge_id,
                                                                self.start_time, self.renew_count)
