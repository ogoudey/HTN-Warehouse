from typing import Any, List
import time
from dataclasses import dataclass



logging = False

transmitting_to_Unity = False
if transmitting_to_Unity:
    from transmitter import ThroughMessage
    


def log(message:Any, end="\n", flush=True, verbose=False):
    if not verbose:
        verbose = logging
    if verbose:
        print(message, end=end)

methods = []
@dataclass
class Location:
    index: str
    next: Any | None = None

    def __eq__(self, other):
        if not isinstance(other, Location):
            return NotImplemented
        return self.index == other.index
    
    def __repr__(self):
        if self.next:
            return f"{{#{str(id(self))[-4:]}: {self.index}}}"
        return f"#{str(id(self))[-4:]}: {self.index}"

@dataclass
class Container:
    name:str
    location: Location | None = None

    def __repr__(self):
        return f"{self.name}: {self.location.index}"
        #return f"Container #{str(id(self))[-4:]}: {self.location.index}"

    def as_moved(self, l:Location):
        return Container(self.name, l)

@dataclass
class FuelLevel:
    index: str | None = None

@dataclass
class Robot:
    name: str
    location: Location | None = None
    fuel: FuelLevel | None = None
    carrying: Container | None = None
    projected_state: "Robot" = None

    def __repr__(self):
        return f"{self.name}:{self.fuel.index}: {self.location.index}"

        if self.carrying:
            return f"Robot: {self.location.index} and carrying: {id(self.carrying)}"
        return f"Robot: {self.location.index}"
    
    def as_carrying(self, c: Container):
        self.projected_state = Robot(self.name, self.location, self.fuel, carrying=c)
        return Robot(self.name, self.location, self.fuel, carrying=c, projected_state=self.projected_state)

    def as_moved(self, l:Location):
        if self.carrying:
            self.projected_state = Robot(self.name, l, self.fuel, carrying=Container(self.carrying.name, l))
            return Robot(self.name, l, self.fuel, carrying=Container(self.carrying.name, l), projected_state=self.projected_state)
        self.projected_state = Robot(self.name, l, self.fuel)
        return Robot(self.name, l, self.fuel, projected_state=self.projected_state)
    
    def refuel(self):
        self.fuel.index = "H"

    def as_refueled(self):
        self.projected_state = Robot(self.name, self.location, FuelLevel("H"), projected_state=self.projected_state)
        return Robot(self.name, self.location, FuelLevel("H"), projected_state=self.projected_state)

    def with_reduced_fuel(self):
        
        self.projected_state = Robot(self.name, self.location, FuelLevel(self.reduce_fuel()), projected_state=self.projected_state)
        return Robot(self.name, self.location, FuelLevel(self.reduce_fuel()), projected_state=self.projected_state)

    def reduce_fuel(self):
        log(f"Reducing fuel from {self.fuel.index}")
        if self.fuel.index == "H":
            return "L"
        elif self.fuel.index == "L":
            return "0"
        elif self.fuel.index == "0":
            return "0"

def precondition(func):
    func.is_precondition = True
    return func

compound_tasks = []

def compound_task(func):
    func.is_compound = True
    func.is_primitive = False
    func.is_task = True
    compound_tasks.append(func)
    return func

def primitive(func):
    func.is_task = True
    func.is_primitive = True
    func.is_compound = False
    return func


def method(func):
    global methods
    methods.append(func)
    return func

class Task:
    func: Any
    def __init__(self, func: Any, items: dict[str, Any]):
        self.func = func
        self.is_primitive = func.is_primitive
        self.dict = items
    
    def __getitem__(self, key):
        return self.dict[key]
    
    def __call__(self, args):
        log(f"{self.func.__name__} called with {list(args.keys())}")
        self.fulfill_argument_slots(args)
        #self.func(*list(self.dict.values()))
    
    def fulfill_argument_slots(self, arguments):
        assert self.is_primitive
        annotations = self.func.__annotations__
        args = []
        for k, v in annotations.items():
            #input(f"{k}, {v}")
            if v == Location:
                try:
                    args.append(self.dict[k])
                    continue
                except KeyError:
                    raise KeyError(f"Key {k} does not appear in task arguments: {self.dict}")
            if v == Container:
                try:
                    if arguments['r'].carrying:
                        container = arguments['r'].carrying
                    else:
                        container = self.detect_container(arguments)
                    args.append(container)
                    continue
                except KeyError:
                    raise KeyError(f"Could not identify container to fulfill {self.func}.")
            if v == FuelLevel:
                try:
                    args.append(self.dict[k])
                    continue
                except KeyError:
                    raise KeyError(f"Key {k} does not appear in task arguments: {self.dict}")
            try:
                args.append(arguments[k])
            except KeyError:
                raise KeyError(f"Key {k} does not appear in world arguments: {arguments}. {v} not identified.")
        log(f"Args: {args}")
        self.func(*args)
    
    def detect_container(self, arguments):
        log(f"Detecting container...")
        robot = arguments['r']
        for k, v in arguments.items():
            #input(f"{k} {v}")
            if hasattr(v, "location"):
                if v.location == robot.location:
                    if type(v) == Container:
                        log(f"Detected {v}")
                        return v


@precondition
def at(r: Robot, l: Location):
    return r.location == l

@precondition
def connected(l1: Location, l2: Location):
    return l1.next == l2

@precondition
def destination(c: Container, l: Location):
    return container_at(c, l)

@precondition
def has(r: Robot, c: Container):
    return r.carrying == c

@precondition
def container_at(c: Container, l: Location):
    return c.location == l

@precondition
def fuel_level(r: Robot, level: FuelLevel):
    return r.fuel == level

class PreconditionException(Exception):
    pass

@compound_task
def move(r: Robot, l1: Location, l2: Location):
    """Move the robot r from the location l1 to the location l2."""
    if r.fuel.index == "0":
        log(f"Robot is out of fuel - cannot move to {l2}")
        raise PreconditionException(f"Robot is out of fuel - cannot move to {l2}")
        return False
    log(f"Moving from {l1} to {l2}", end="")
    if not r.location.index == l1.index:
        raise PreconditionException(f"Robot at {r.location.index}, not {l1.index}")
    
    r.location = l2
    if r.carrying:
        log(f" while also carrying {r.carrying} to {l2}")
        r.carrying.location = l2
    else:
        log("")
    r.fuel.index = r.reduce_fuel()
    return True

@primitive
def refuel(r: Robot, level: FuelLevel):
    """Set the fuel level of the robot r to the level"""
    r.fuel.index = level.index
    return True

@primitive
def pick_up(r: Robot, c: Container):
    """The robot r picks up the container c at the current location."""
    if not r.location == c.location:
        raise PreconditionException(f"Container at {c.location.index}, not {r.location.index}")
    log(f"{r} is picking up {c}")
    r.carrying = c
    c.location = r.location
    return True

@primitive
def drop_down(r: Robot, c: Container):
    """The robot r drops down the container c at the current location"""
    log(f"{r} is dropping {c}")
    r.carrying = None
    c.location = c.location
    return True

@compound_task
def single_delivery(c: Container, l1: Location, l2: Location):
    if not c.location == l1:
        raise PreconditionException(f"Container at {c.location.index}, not {l1.index}")
    return Task(single_delivery, {"c": c, "l1": l1, "l2": l2})

@compound_task
def multi_delivery(c1: Container, l1: Location, c2: Container, l2: Location):
    return Task(multi_delivery, {"c1": c1, "l1": l1, "c2": c2, "l2": l2})


### ========== Methods ========== ###

class TaskException(Exception):
    # A useful exception for when a method is not applicable; not representative of an error
    pass
    
class FuelFullException(Exception):
    # Raised if fuel is full when m_refuel is applied. To stop infinite refueling.
    pass

class MovingWithLowFuelException(Exception):
    # Another "helpful" exception to avoid plans where the robot runs out of fuel.
    pass

class NotCompoundException(Exception):
    # A more-real exception, raised if method is applied to a primitive task.
    pass


@method
def m_all_delivered(
    task=Task
) -> List[Any]:
    if not task.func == multi_delivery:
        raise TaskException(f"Task is a {task.func.__name__}, not {multi_delivery.__name__}")
    try:
        c1: Container = task["c1"]
        l1 = task["l1"]
        c2: Container = task["c2"]
        l2 = task["l2"]
    except KeyError as e:
        log(e)
        raise KeyError(str(e) + str(task.dict))
    log(f"m_all_delivered: {task.dict}", end=" ")
    l0 = c1.location
    l2_minus_1 = c2.location
    return [
        Task(single_delivery, {"c": c1, "l1": l0, "l2": l1}),
        Task(single_delivery, {"c": c2, "l1": l2_minus_1, "l2": l2})
    ]

@method
def m_single_delivered(
    task=Task
) -> List[Any]:
    if not task.func == single_delivery:
        raise TaskException(f"Task is a {task.func.__name__}, not {single_delivery.__name__}")
    c = task["c"]
    l2 = task["l1"]
    l3 = task["l2"]
    global r
    
    if r.projected_state:
        r = r.projected_state
    l1 = r.location
    log(f"m_single_delivered: {task.dict}", end=" ")
    # Add refuels intermitently - hacky?
    return [
        Task(move, {"r": r, "l1": l1, "l2": l2}),
        Task(refuel, {"r": r, "level": FuelLevel("H")}),
        Task(pick_up, {"r": r.as_moved(l2), "c": c}),
        Task(move, {"r": r.as_carrying(c).as_moved(l2), "l1": l2, "l2": l3}),
        Task(refuel, {"r": r.as_carrying(c).as_moved(l3), "level": FuelLevel("H")}),
        Task(drop_down, {"r": r.as_moved(l3), "c": c.as_moved(l3)})
    ]

@method
def m_move(
    task=Task
) -> List[Any]:
    if not task.func == move:
        raise TaskException(f"Task is a {task.func.__name__}, not {single_delivery.__name__}")
    if task.func.is_primitive:
        raise NotCompoundException(f"Task is not compound. No method needed.")
    
    r: Robot = task["r"]
    #if r.projected_state:
    #    r = r.projected_state
    log(f"Fuel at move {r.fuel.index}")
    l1 = task["l1"]
    l2 = task["l2"]

    if r.fuel.index == "0":
        raise TaskException(f"Won't m_move from {l1} with no fuel.")

    #if r.fuel.index == "L":
    #    raise TaskException(f"Won't m_move from {l1} with low fuel.")

    log(f"m_move: {task.dict}", end=" ")
    if l1 == l2:
        return []

    l1_point_5 = l1.next

    if connected(l1, l2):
        task.is_primitive = True
        return [task]
    else:
        return [
            Task(move, {"r": r, "l1": l1, "l2": l1_point_5}),
            Task(move, {"r": r.as_moved(l1_point_5).with_reduced_fuel(), "l1": l1_point_5, "l2": l2})
        ]

@method
def m_refuel(
    task=Task
) -> List[Task]:
    if not task.func == move:
        raise TaskException(f"Task is a {task.func.__name__}, not {single_delivery.__name__}")
    r: Robot = task["r"]
    l1 = task["l1"]
    l2 = task["l2"]
    
    if r.fuel.index == "H":
        raise FuelFullException("Fuel is already full. No need to refuel.")

    return [
            Task(refuel, {"r": r, "level": FuelLevel("H")}),
            Task(move, {"r": r.as_refueled(), "l1": l1, "l2": l2})
        ]
    

### Helper functions for solver
def is_solution(plan: List[Task]):
    for task in plan:
        if not task.is_primitive:
            return False
    return True

def get_compound(plan: List[Task]):
    for task in plan:
        if not task.is_primitive:
            return task

###


class S:
    ### Class which sets Facts
    @staticmethod
    def at(r, l):
        r.location = l
    @staticmethod
    def container_at(c, l):
        c.location = l
    @staticmethod
    def fuel_level(r, level):
        r.fuel = level
    @staticmethod
    def connect(l1, l2):
        l1.next = l2


if __name__ == "__main__":

    ### Initialize environment ###
    lA = Location("A")
    lB = Location("B")
    lC = Location("C")
    lD = Location("D")
    S.connect(lA, lB)
    S.connect(lB, lC)
    S.connect(lC, lD)
    S.connect(lD, lA)

    r: Robot = Robot("Robot")
    S.at(r, lA)
    c1: Container = Container("ContainerA")
    S.container_at(c1, lA)
    c2: Container = Container("ContainerB")
    
    S.container_at(c2, lC)
    fuel: FuelLevel = FuelLevel("L")
    S.fuel_level(r, fuel)


    ### Task assignment ###
    root: List[Task] = [multi_delivery(c1, lD, c2, lB)]

    root_p = f"{root[0].func.__name__}" # for logging
    log(root_p, end="\r")

    ### Solving/decomposition ###
    
    plan = root
    while not is_solution(plan):
        compound: Task = get_compound(plan)
        for m in methods:
            #input() # Uncomment to step through decomposition
            try:
                log(f"Trying {m}")
                subtasks: List[Task] = m(compound)
                log(f"Turned '{compound.func.__name__}' into {[task.func.__name__ for task in subtasks]}")
            except TaskException as e:
                log(e)
                continue
            
            idx = plan.index(compound)
            for subtask_idx in range(0, len(subtasks)):
                plan.insert(idx + subtask_idx, subtasks[subtask_idx])
            plan.remove(compound)
            log(f"=> {[task.func.__name__ for task in subtasks]}")
            log(f"{root_p} => {[(task.func.__name__, task.dict) for task in plan]}", end="\r", flush=True)
            break
    log(f"{root_p} => {[task.func.__name__ for task in plan]}")

    ### Execution ###
    
    def goal():
        # Execution helper
        if container_at(c1, lD) and container_at(c2, lB) and not r.carrying == c1 and not r.carrying == c2:
            return True
        return False

    def state():
        # Helper for printing or setting state in Unity
        return [r, c1, c2]

    ### (Reinitialize) ###
    S.at(r, lA)
    S.container_at(c1, lA)    
    S.container_at(c2, lC)

    arguments = {"r": r, "c1": c1, "c2": c2}
    log(r)

    if transmitting_to_Unity:
        shared = {"target_message": str(state())}
        through_thread = ThroughMessage(shared)
        through_thread.start()
        while not through_thread.up:
            time.sleep(1)
        time.sleep(3.0)

    while not goal():
        if transmitting_to_Unity:
            shared["target_message"] = str(state())
            time.sleep(3.0)

        log(state(), verbose=True)
        succeeded = plan.pop(0)(arguments)

            
