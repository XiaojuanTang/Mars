## Skill Library
Motivated by [JARVIS-1](https://arxiv.org/abs/2311.05997) and [Voyager](https://arxiv.org/abs/2305.16291), we have simplified the framework to adapt to Mars, calling it the Skill Library. The implementation of the Skill Library can be found in the `skill_library` folder.
## Training
The training process involves 5 episodes, during which skills are incrementally stored in memory.json. The command to run the training is:
```sh
python run.py --load_world final_world/world_ach --episode 5 
```
The logs are stored in the corresponding load_world folder, e.g., final_world/world_ach.

## Testing
After training, the agent can be tested with the learned skill library `memory.json`. The command is:
```sh
python test.py --load_world final_world/world_ach --memory_path final_world/world_ach/memory.json
```