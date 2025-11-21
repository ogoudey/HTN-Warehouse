# AI Planning Homework 3 - Task Network
### Assumptions about the solver:
The task is "solved" with decomposition. The process goes from left to right applying to the first **compound** task the first method that is **applicable**. The plan is considered to be a solution when all its tasks are **primitive**. Thus:
```
multi_delivery => ['refuel', 'pick_up', 'move', 'refuel', 'move', 'move', 'refuel', 'drop_down', 'move', 'refuel', 'move', 'move', 'refuel', 'pick_up', 'move', 'refuel', 'move', 'move', 'refuel', 'drop_down']
```

## Running
To get the above results, do:
```
python3 tasks.py
```
To change verbosity, change the `logging` variable at the top of `tasks.py` to `True`.

If the Unity environment is set up, change `transmitting_to_Unity` to `True`.

### Unity Demo
Project structure:

<img width="123" height="118" alt="image" src="https://github.com/user-attachments/assets/98fbba91-8cdb-45ed-bada-8c4d53a8bbb7" />
<br>
<br>

Video demo:

[warehouse THN2_2x.webm](https://github.com/user-attachments/assets/4975aeeb-c593-4118-ae9d-36ba19c6e27e)
