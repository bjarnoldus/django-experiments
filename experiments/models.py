from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from django.db.models import F

from jsonfield import JSONField

import random
import json

from experiments.dateutils import now
from experiments import conf


CONTROL_STATE = 0
ENABLED_STATE = 1
TRACK_STATE = 3

STATES = (
    (CONTROL_STATE, 'Default/Control'),
    (ENABLED_STATE, 'Enabled'),
    (TRACK_STATE, 'Track'),
)

class Counter(models.Model):
    key = models.CharField(primary_key=True, max_length=128)
    hash = models.CharField( max_length=96)
    field = models.CharField( max_length=20)
    count = models.IntegerField(default=0,blank=False,null=False)

class Count():    
    @classmethod
    def next(cls, hash="default", field="default", count = 1):
        key = "%s:%s" % (hash, field)
        try:
            Counter.objects.filter(pk = key).update(count = (F('count') + count))
            return Counter.objects.get(pk = key).count
        except Counter.DoesNotExist:
            return Counter.objects.create(key = key, hash=hash, field=field, count = count).count

    @classmethod
    def get(cls, hash="default", field="default"):
        key = "%s:%s" % (hash, field)
        try:
            return Counter.objects.get(pk = key).count
        except Counter.DoesNotExist:
            return Counter.objects.create(key = key, hash=hash, field=field, count = 0).count

    @classmethod
    def getall(cls, hash="default"):
        try:
            return Counter.objects.filter(hash = hash)
        except Counter.DoesNotExist:
            return None


    @classmethod
    def delete(cls, hash="default"):
        try:
            objects = Counter.objects.filter(hash = hash)
            
            for o in objects:
                o.delete()
                
            objects = Counter.objects.filter(hash = hash)
            return None
        except Counter.DoesNotExist:
            return None

    @classmethod
    def deletefield(cls, hash="default", field="default"):
        key = "%s:%s" % (hash, field)
        try:
            return Counter.objects.get(pk = key).delete()
        except Counter.DoesNotExist:
            return None
        
    @classmethod
    def len(cls, hash="default"):
        try:
            return Counter.objects.filter(hash = hash).count()
        except Counter.DoesNotExist:
            return 0
        
    @classmethod
    def next_hex(cls, key = 'default:default'):
        return hex(Counter.next(key)).replace('0x', '').replace('L', '')
    
    def __unicode__(self):
        return u'%s = %s' % (self.pk, self.count)
    

class Experiment(models.Model):
    name = models.CharField(primary_key=True, max_length=128)
    description = models.TextField(default="", blank=True, null=True)
    alternatives = JSONField(default={}, blank=True)
    relevant_chi2_goals = models.TextField(default="", null=True, blank=True)
    relevant_mwu_goals = models.TextField(default="", null=True, blank=True)

    state = models.IntegerField(default=CONTROL_STATE, choices=STATES)

    start_date = models.DateTimeField(default=now, blank=True, null=True, db_index=True)
    end_date = models.DateTimeField(blank=True, null=True)

    def is_displaying_alternatives(self):
        if self.state == CONTROL_STATE:
            return False
        elif self.state == ENABLED_STATE:
            return True
        elif self.state == TRACK_STATE:
            return True
        else:
            raise Exception("Invalid experiment state %s!" % self.state)

    def is_accepting_new_users(self):
        if self.state == CONTROL_STATE:
            return False
        elif self.state == ENABLED_STATE:
            return True
        elif self.state == TRACK_STATE:
            return False
        else:
            raise Exception("Invalid experiment state %s!" % self.state)

    def ensure_alternative_exists(self, alternative, weight=None):
        if alternative not in self.alternatives:
            self.alternatives[alternative] = {}
            self.alternatives[alternative]['enabled'] = True
            self.save()
        if weight is not None and 'weight' not in self.alternatives[alternative]:
            self.alternatives[alternative]['weight'] = float(weight)
            self.save()

    @property
    def default_alternative(self):
        for alternative, alternative_conf in self.alternatives.items():
            if alternative_conf.get('default'):
                return alternative
        return conf.CONTROL_GROUP

    def set_default_alternative(self, alternative):
        for alternative_name, alternative_conf in self.alternatives.items():
            if alternative_name == alternative:
                alternative_conf['default'] = True
            elif 'default' in alternative_conf:
                del alternative_conf['default']

    def random_alternative(self):
        if all('weight' in alt for alt in self.alternatives.values()):
            return weighted_choice([(name, details['weight']) for name, details in self.alternatives.items()])
        else:
            return random.choice(list(self.alternatives.keys()))

    def __unicode__(self):
        return self.name

    def to_dict(self):
        data = {
            'name': self.name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'state': self.state,
            'description': self.description,
            'relevant_chi2_goals': self.relevant_chi2_goals,
            'relevant_mwu_goals': self.relevant_mwu_goals,
            'default_alternative': self.default_alternative,
            'alternatives': ','.join(self.alternatives.keys()),
        }
        return data

    def to_dict_serialized(self):
        return json.dumps(self.to_dict(), cls=DjangoJSONEncoder)


class Enrollment(models.Model):
    """ A participant in a split testing experiment """
    user = models.ForeignKey(getattr(settings, 'AUTH_USER_MODEL', 'auth.User'))
    experiment = models.ForeignKey(Experiment)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(null=True)
    alternative = models.CharField(max_length=50)

    class Meta:
        unique_together = ('user', 'experiment')

    def __unicode__(self):
        return u'%s - %s' % (self.user, self.experiment)


def weighted_choice(choices):
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        upto += w
        if upto >= r:
            return c


