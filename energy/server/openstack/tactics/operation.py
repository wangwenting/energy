import time
import threading
import copy
import eventlet
from eventlet.timeout import Timeout
from oslo.config import cfg

from energy.common import log
from energy.operation.novaworker import NovaWorker

eventlet.monkey_patch()
LOG = log.getLogger(__name__)


class Element(object):
    def __init__(self, id, src, size):
        self.id = id
        self.src = src
        self.size = size

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash(self.id)


class NovaOperatorFactory(object):
    def __init__(self):
        pass

    def create(self):
        return NovaOperator()


class OperatorBase(object):

    def __init__(self):
        pass

    def excute(self, plan, notify_func=None, is_asycn=False):
        pass


class NovaOperator(OperatorBase):

    def __init__(self):
        super(OperatorBase, self).__init__()

    def excute(self, action, notify_func=None, timeout=60, is_async=False):
        vm_id = action.id
        LOG.info("start excuting: id:%s, src:%s, des:%s" % (vm_id, action.src, action.des))
        result = {}
        result['state'] = "raw"
        with Timeout(timeout, False):
            result['state'] = "pre_migrate"
            try:
                LOG.debug("call nova interface: id:%s" % action.id)
                worker = NovaWorker()
                worker.live_migration(action.id, action.des)
            except Exception as e:
                LOG.error("excuting failed: reason:%s" % e)
                result['state'] = "failed"
                return result

        LOG.debug("vm:%s migrate result %s" % (action.id, result["state"]))
        return result


class Action(object):
    def __init__(self, id, src, des, ele):
        self.id = id
        self.src = src
        self.des = des
        self.ele = ele


class PlanGenerator(object):

    def __init__(self):
        pass

    def generate(self, src, des, capacity, remain_capacity):
        assert len(src) == len(des)
        raw_capacity = copy.deepcopy(remain_capacity)

        temp_pair = capacity.popitem()
        size_dimension = len(temp_pair[1])
        capacity[temp_pair[0]] = temp_pair[1]
        plan = Plan(capacity.keys())

        statble = [e for e in src if src[e] == des[e]]
        for s in statble:
            del src[s]
            del des[s]

        sorted_des = sorted(des, key=lambda ele: ele.size[1])

        while src:
            action_groups = dict((k, []) for k in plan.action_groups_dict)

            for ele in copy.copy(sorted_des):
                ele_des = des[ele]
                print(ele.size)
                print(remain_capacity)
                if all(ele.size[k] <= remain_capacity[ele_des][k] for k in xrange(size_dimension)):
                    remain_capacity[ele_des][0] -= ele.size[0]
                    remain_capacity[ele_des][1] -= ele.size[1]
                    action = Action(ele.id, src[ele], des[ele], ele)
                    action_groups[ele_des].append(action)
                    sorted_des.remove(ele)
                    del des[ele]

            for ele in [e for e in src if e not in des]:
                remain_capacity[src[ele]][0] += ele.size[0]
                remain_capacity[src[ele]][1] += ele.size[1]
                del src[ele]

            for k in action_groups:
                plan.action_groups_dict[k].actions += (action_groups[k] + [None])
        plan.add_resources(raw_capacity)
        return plan


class ActionGroup(object):

    def __init__(self):
        self.resource = [0, 0]
        self.actions = []

    def pop_satisfied_actions(self):
        actions = []
        while self.actions and not self.actions[0]:
            self.actions.pop(0)
        for action in self.actions:
            if not action:
                break
            if action.ele.size[0] <= self.resource[0] and action.ele.size[1] <= self.resource[1]:
                actions.append(action)
                self.resource[0] = self.resource[0] - action.ele.size[0]
                self.resource[1] = self.resource[1] - action.ele.size[1]
        [self.actions.remove(action) for action in actions]
        return actions

    def group_done(self):
        if not self.actions:
            return self.resource
        else:
            return None

    def add_resource(self, capacity):
        assert len(self.resource) == len(capacity)
        for i in range(len(capacity)):
            self.resource[i] = capacity[i]


class Plan(object):
    """plan  for action groups
    """

    def __init__(self, groups):
        self.result = {}
        self.action_groups_dict = dict((name, ActionGroup()) for name in groups)
        self.result["timeout"] = []

    def action_done(self, action, result):
        if result["state"].lower() == "success":
            self.action_groups_dict[action.src].add_resource(action.ele.size)

        self.result["timeout"].remove(action)
        self.result.setdefault(result["state"], []).append(action)

    def pop_actions(self):
        actions = []
        for group in self.action_groups_dict.values():
            actions += group.pop_satisfied_actions()
        self.result["timeout"] += actions
        return actions

    def add_resources(self, resources):
        for r in resources:
            self.action_groups_dict[r].add_resource(resources[r])


list_lock = threading.RLock()

default_operator_factory = NovaOperatorFactory()


class ActionScheduler(object):

    def __init__(self, engine, excutor_factory=default_operator_factory):
        self.engine = engine

    def schedule(self):
        def excute_action(action):
            excutor = default_operator_factory.create()
            result = excutor.excute(action, self.engine.action_done)
            self.engine.thread_count = self.engine.thread_count - 1
            self.engine.action_done(action, result)

        actions = list(self.engine.action_list)
        for action in actions:
            LOG.info("action added to queue id:%s, src:%s, des:%s" % (action.id, action.src, action.des))
            self.engine.action_list.remove(action)
            LOG.info("spawn thread[%s] for action id:%s" % (self.engine.thread_count, action.id))
            self.engine.thread_count = self.engine.thread_count + 1
            eventlet.spawn(excute_action, action)
        LOG.info("actions count %s" % len(actions))
        return actions


class ExcutorEngine(object):

    def __init__(self):
        eventlet.monkey_patch()
        self.stat = "free"
        self.thread_count = 0
        self.done = False

    def excute_plan(self, plan, action_callback=None, plan_callback=None):
        LOG.info("start excute plan")
        print("start excute plan")
        if (self.stat != "free"):
            return False
        self.action_callback = action_callback
        self.plan_callback = plan_callback
        self.stat = "excuting"
        self.plan = plan
        self.action_list = []
        self._do_excute()
        return True

    def _do_excute(self):
        for action in self.plan.pop_actions():
            self.action_list.append(action)
        print("action list %s" % self.action_list)
        if not self.action_list:
            self.plan_done()
            return
        self.action_scheduler = ActionScheduler(self)
        print("ActionScheduler schedule")
        self.action_scheduler.schedule()

    def plan_done(self):
        self.stat = "free"
        if self.plan_callback:
            self.plan_callback(self.plan)
        LOG.info("Plan done")
        self.done = True

    def action_done(self, action, result):
        LOG.info("Action done")
        if self.action_callback:
            self.action_callback(action, result)
        actions = self.plan.pop_actions()
        if not actions and not self.thread_count:
            self.plan_done()
            return
        self.action_list += actions
        self.action_scheduler.schedule()
