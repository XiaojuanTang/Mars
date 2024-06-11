## induction_from_reflexion_std
Based on Skill Library, we introduce the Induction from Reflexion (IFR) module to induce rules from the skill library. The implementation of the IFR module can be found in the `induction_from_reflexion_std` and `induction_from_reflexion_CC` folder.
## Training
The training process involves 5 episodes, during which skills are incrementally stored in memory.json. The command to run the training is:
```sh
python run.py --load_world final_world/world_ach --episode 5 
```
The logs are stored in the corresponding load_world folder, e.g., final_world/world_ach.

## Testing
After training, the agent can be tested with the learned skill library `memory.json` and induced rules `reflection.txt`. The command is:
```sh
python test.py --load_world final_world/world_ach --memory_path final_world/world_ach/induction_from_reflexion_std/202405312119-gpt-4-0125-preview
```