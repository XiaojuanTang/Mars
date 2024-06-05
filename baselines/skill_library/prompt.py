

## propose task from task pool
TASK_SELECTOR_SYS = '''You are a helpful assistant that choose the next task from the task pool to do in the 2D game. My ultimate goal is to discover as many diverse things as possible, accomplish as many diverse tasks as possible while ensuring survival and become the best player in the world.

Task pool: [collect coal, collect diamond, collect drink, collect iron, collect sapling, collect stone, collect wood, kill skeleton, kill zombie, kill cow, eat plant, make iron pickaxe, make iron sword, make stone pickaxe, make stone sword, make wood pickaxe, make wood sword, place furnace, place plant, place stone, place table, wake up]

I will give you the following information:
Player's in-game observation: including the player's status, nearby blocks and the inventory.
Completed tasks so far: ...
Failed tasks: ...

Based on this information, you should propose the next task for the player to do.
You must follow the following criteria:
1) The task should be diverse and challenging, but not too hard. It should be something that the player can accomplish in the next few steps.
2) You may sometimes need to repeat some tasks if you need to collect more resources to complete more difficult tasks. Only repeat tasks if necessary.
3) The task should be related to the player's current status, nearby blocks and inventory.

You should only respond in the format as described below:
RESPONSE FORMAT:
Reasoning: Based on the information I listed above, do reasoning about what the next task should be.
Task: The next task.

Here's an example response:
Reasoning: The inventory is empty now, chop down a tree to get some wood.
Task: collect wood
'''         

## plan the specific task
TASK_PLANNER_SYS = '''You are a helper AI agent in the 2D game. Based on your current inventory and observations, you need to generate the sequences of subgoals for a certain task. Please refer the history dialogue to give the plan consist of template. Do not explain or give any other instruction.

You must follow the criteria below:
1) You should only mine [stone, coal, iron, tree, diamond, water, lava, grass, sand, ripe-plant] blocks.
2) You should only attack movable creatures.
3) You should only place [stone, table, furnace, sapling] blocks.
4) You should only craft [wood pickaxe, stone pickaxe, iron pickaxe, wood sword, stone sword, iron sword] tools.
5) You should choose available subgoals to complete the task.
6) You are probably provided some past successful plans to refer to.
8) Not all creatures are friendly. When you are attacked, please attack back.
9) You should only perform the subgoals that are feasible based on the current inventory and observations.
10) This is a 2D game, so when you encounter a obstacle, you should mine it or place a block to build a "path" or make a detour.

Here are available subgoals:
mine(block_name, amount) # mine amount blocks of the block_name. 
attack(creature, amount) # attack the amount creature that can move. Creature include zombie, skeleton, cow, etc.
sleep(); # put the player to sleep.
place(block_name); # place the block. Note you need not craft table and furnace, you can place them directly.
make(tool_name); # craft a tool.
explore(direction, steps); # the player explore in the direction for steps.

Here are some example for output format:
The task is to collect wood. The plan is below:
# step 1: mine("tree", 1) # mine the tree block to get wood

The task is to collect sapling. The plan is below:
# step 1: mine("grass", 1) # mine the grass block to potentially get the sapling
'''

TASK_MEMORY_ASSISTANT = '''
Here are some successful plans that you can refer to:
{memory}
'''

TASK_PLANNER_USER_1 = '''You are on the grass.
You see: (object with coordinate)
grass is in front of me.
<grass(-1, 0), grass(1, 0), grass(0, -1), grass(0, 1), tree(-4, 3), cow(4, 1)>
Your status: <health: 9/9, food: 9/9, drink: 9/9, energy: 9/9>
You have nothing in your inventory.
Your task is to: collect wood. Please generate the sequences of sub-goals to complete the task.
'''

TASK_PLANNER_ASSIST_1 = '''The plan is below:
# step 1: mine("tree", 1) # mine the tree block
'''

TASK_PLANNER_USER_2 = '''You are on the grass.
You see: (object with coordinate)
grass is in front of me.
<grass(-1, 0), grass(1, 0), grass(0, -1), grass(0, 1), grass(-4, 3)>
Your status: <health: 9/9, food: 9/9, drink: 9/9, energy: 9/9>
You have nothing in your inventory.
Your task is to: collect sapling. Please generate the sequences of sub-goals to complete the task.
'''

TASK_PLANNER_ASSIST_2 = '''The plan is below:
# step 1: mine("grass", 1) # mine the grass block to potentially get the sapling
# step 2: mine("grass", 1) # mine the grass block again to potentially get the sapling
'''

TASK_PLANNER_USER_TEMPLATE = '''Your task is to: {task}. Please generate the sequences of sub-goals to complete the task.
'''

TASK_REPLANNER_USER = '''Please fix the above errors and replan the task [{task}].
'''
REFLECTION_SYS = '''Here are some actions that the agent fails to perform in the 2D game. Please give the explanation of action execution failure according to the current inventory information of the agent and history dialogue.

You must follow the criteria below:
1) You should only mine [stone, coal, iron, tree, diamond, water, lava, grass, sand, ripe-plant] blocks.
2) You should only attack movable creatures.
3) You should only place [stone, table, furnace, sapling] blocks.
4) You should only craft [wood pickaxe, stone pickaxe, iron pickaxe, wood sword, stone sword, iron sword] tools.
5) Not all creatures are friendly. When you are attacked, please attack back.
6) This is a 2D game, so when you encounter a obstacle, you should mine it or place a block to build a "path" or make a detour.

Here are some examples:
Question:
I failed on mine("stone", 1) # mine 1 stone block
Current Observations: 
I am on the grass.
I see: (object with coordinate)
stone is in front of me.
<grass(-1, 0), grass(1, 0), stone(0, -1), grass(0, 1), tree(-4, 3), cow(4, 1)>
My status: <health: 9/9, food: 9/9, drink: 9/9, energy: 9/9>
I have nothing in your inventory.
Answer:
Because mining stone needs to use the tool wook pickaxe, but I does not have the tool in the inventory. I needs to craft a wood pickaxe first.

Question:
I failed on mine("stone", 3) # mine 3 stone block
Current observation: 
I am on the grass.
I see: (object with coordinate)
water is in front of me.
<grass(-1, 0), grass(1, 0), water(0, -1), grass(0, 1), tree(0, -2), cow(4, 1)>
My status: <health: 9/9, food: 9/9, drink: 9/9, energy: 9/9>
My inventory: <wood pickaxe: 1, stone: 2>
Answer:
I am facing water and cannot mine the stone block. I needs to bypass the water block or place a "walkable" block to cross it.

Question:
I failed on craft("wood pickaxe") # craft a wood pickaxe
Current observation: 
I am on the grass.
I see: (object with coordinate)
grass is in front of me.
<grass(-1, 0), grass(1, 0), grass(0, -1), grass(0, 1), tree(-4, 3), cow(4, 1)>
My status: <health: 9/9, food: 9/9, drink: 9/9, energy: 9/9>
My inventory: <wood: 1>
Answer:
Because crafting a wood pickaxe needs 1 wood and place a crafting table at the front of me. But I have not placed the crafting table yet. I needs to place the crafting table first.

Question:
I failed on place("table") # place a crafting table in front of the player
Current observation: 
I am on the grass.
I see: (object with coordinate)
zombie is in front of me.
<grass(-1, 0), zombie(1, 0), zombie(0, -1), grass(0, 1), grass(-1, -1), grass(1, -1), grass(-1, 1), grass(1, 1), stone(0, -2), path(1, -2), cow(2, 1), skeleton(-3, -3), zombie(-2, 1), zombie(2, 0)>
My status: <health: 3/9, food: 9/9, drink: 0/9, energy: 2/9>
My inventory: <wood: 5, stone: 5, wood_pickaxe: 3, wood_sword: 1>
Answer:
Because I am surrounded by zombie and cannot place the table on the ground. I needs to remove the zombie and also ensure my safety.

Question:
I succeeded on all steps [# step 1: mine("tree", 5)] but failed to complete the task [collect sapling].
Answer:
Tree block cannot drop sapling. I needs to mine the grass block to potentially get the sapling. 

Question:
I succeeded on all steps [# step 1: mine("grass", 1)] but failed to complete the task [collect sapling].
Answer:
Mining grass block is not always successful to get the sapling. I needs to mine the grass block again and again to potentially get the sapling.

Question:
I failed on # step 1: attack("cow", 1) # attack the cow to kill it.
Current observation: 
I am on the grass.
I see: (object with coordinate)
tree is in front of me.
<zombie(-1, 0), tree(1, 0), tree(0, -1), grass(0, 1), grass(-1, -1), tree(1, -1), water(-1, 1), grass(1, 1), sand(-3, 0), cow(1, -2), skeleton(-1, -3), arrow(-1, -2)>
My status: <health: 2/9, food: 0/9, drink: 1/9, energy: 8/9>
My inventory: <sapling: 3, wood: 6, stone: 2, wood_pickaxe: 1, wood_sword: 1, stone_sword: 1>
Answer: Because I am surrounded by tree and zombie, I should attack the zombie first to ensure my safety and then mine the tree block to get to the cow.
'''

REFLECTION_USER_1 = '''Failed Action: mine("stone", 1) # mine 1 stone block
Current Observations: 
I am on the grass.
I see: (object with coordinate)
stone is in front of me.
<grass(-1, 0), grass(1, 0), stone(0, -1), grass(0, 1), tree(-4, 3), cow(4, 1)>
My status: <health: 9/9, food: 9/9, drink: 9/9, energy: 9/9>
I have nothing in your inventory.
'''
REFLECTION_ASSIST_1 = '''Because mining stone needs to use the tool wook pickaxe, but I does not have the tool in the inventory. I needs to craft a wood pickaxe first.
'''

REFLECTION_USER_2 = '''Failed Action: mine("stone", 2) # mine 3 stone block
Current Observations: 
I am on the grass.
I see: (object with coordinate)
water is in front of me.
<grass(-1, 0), grass(1, 0), water(0, -1), grass(0, 1), tree(0, -2), cow(4, 1)>
My status: <health: 9/9, food: 9/9, drink: 9/9, energy: 9/9>
My inventory: <wood pickaxe: 1, stone: 2>
'''

REFLECTION_ASSIST_2 = '''Because my inventory has 2 stone blocks, indicating that I have met the requirement of mining stone block and the plan may be feasible. But I am facing the water block, I need to bypass the water block or place a "walkable" block to cross it.'''

# REFLECTION_USER_3 = '''Failed Action: place("table") # place a crafting table in front of the player
# Current Observations: 
# I am on the grass.
# I see: (object with coordinate)
# <grass(-1, 0), grass(1, 0), grass(0, -1) [also in your front], grass(0, 1), tree(-4, 3), cow(4, 1)>
# My status: <health: 9/9, food: 9/9, drink: 9/9, energy: 9/9>
# My inventory: <wood: 1>
# '''

# REFLECTION_ASSIST_3 = '''Because placing table needs two wood blocks and needs me to face the ground. But I only have one wood block in the inventory and I am facing the stone block. I needs to move to the front of the stone block first or go to another place to place the table.'''

REFLECTION_USER_4 = '''Failed Action: craft("wood pickaxe") # craft a wood pickaxe
Current Observations: 
I am on the grass.
I see: (object with coordinate)
grass is in front of me.
<grass(-1, 0), grass(1, 0), grass(0, -1), grass(0, 1), tree(-4, 3), cow(4, 1)>
My status: <health: 9/9, food: 9/9, drink: 9/9, energy: 9/9>
My inventory: <wood: 1>
'''

REFLECTION_ASSIST_4 = '''Because crafting a wood pickaxe needs 1 wood and place a crafting table at the front of me. But I have not placed the crafting table yet. I needs to place the crafting table first.'''

# REFLECTION_USER_TEMPLATE = '''Failed Action: {action}
# Current Observations: 
# {description}
# '''

# "SUCCEED" means that the goal is achieved; "FAILED" means that it is too hard to achieve the goal.
CONTROLLER_SYS = '''You are a helpful assistant trying to play a 2D game. Given the current observation and the goal, you need to generate the action to complete the goal. You can only perform the following actions:
<move_left, move_right, move_up, move_down, do, sleep, place_stone, place_table, place_furnace, place_plant, make_wood_pickaxe, make_stone_pickaxe, make_iron_pickaxe, make_wood_sword, make_stone_sword, make_iron_sword, SUCCEED, FAILED>, where 'do' means to interact the block at front of the player, including mine the block, attack the creature, and drink; "SUCCEED" means that the goal is achieved; "FAILED" means that it is too hard to achieve the goal.

You should follow the criteria below:
1) When the desired item is not immediately visible, it is essential to explore the surroundings to locate it. You can move strategically in the direction where the item is likely to be found.
2) Not all creatures are friendly. When you are attacked, please attack back.
3) When you need to craft tools with table or furnace, if there is table or furnace in the view, please move your position to not more than 2 steps away from it.
4) When table and furnace are needed simultaneously, please place them together and place them on proper terrain.
5) This is a 2D game, so when you encounter a obstacle, you should mine it or place a block to build a "path" or find a detour.
6) When you mine block or attack creature or drink, you must face the block.
7) If you move left, your x-coordinate will decrease by 1; if you move right, your x-coordinate will increase by 1; if you move up, your y-coordinate will increase by 1; if you move down, your y-coordinate will decrease by 1.

You should only respond in the format as described below:
RESPONSE FORMAT:
Reasoning: Based on the information I listed above and history dialogue, do reasoning about how to achieve the goal.
Action: The next action.

Here's an example:
I am on the grass.
I see: (object with coordinate)
grass is in front of me.
<grass(-1, 0), grass(1, 0), grass(0, -1), tree(0, 1), grass(-1, -1), grass(1, -1), grass(-1, 1), grass(1, 1)>
My status: <health: 9/9, food: 9/9, drink: 9/9, energy: 9/9>
I have nothing in your inventory.
Response:
Reasoning: Because the tree is at (0, 1), not in my front. My goal is [mine('tree', 1)]. I should move up to the tree and mine it.
Action: move_up

Here's another example:
I am on the grass.
I see: (object with coordinate)
grass is in front of me.
<grass(-1, 0), grass(1, 0), grass(0, -1), tree(0, 1), grass(-1, -1), grass(1, -1), grass(-1, 1), grass(1, 1)>
My status: <health: 9/9, food: 9/9, drink: 9/9, energy: 9/9>
My inventory: <wood: 1>
Response:
Reasoning: Because my goal is [mine('tree',1) # mine the tree get wood], I have collected the wood. So I achieved the goal.
Action: SUCCEED
'''

CONTROLLER_USER_TEMPLATE = "My goal is [{subgoal}]. Please generate the reasoning steps and next action to achieve the goal."

