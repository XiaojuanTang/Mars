from utils import *
from mars.api.envWrapper import *
from mars.api.controller import *
import argparse
import pathlib

import pygame
import mars, os, shutil


from datetime import datetime
from agent import *

import copy

# main function
def main():
    boolean = lambda x: bool(['False', 'True'].index(x))
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--area', nargs=2, type=int, default=(64, 64))
    parser.add_argument('--view', type=int, nargs=2, default=(9, 9))
    parser.add_argument('--length', type=int, default=1000)
    parser.add_argument('--health', type=int, default=9)
    parser.add_argument('--window', type=int, nargs=2, default=(600, 600))
    parser.add_argument('--size', type=int, nargs=2, default=(0, 0))
    parser.add_argument('--load_world', type=pathlib.Path, default="final_world/world_terr_ach")
    parser.add_argument('--model', type=str, default="induction_from_reflexion_CC")
    parser.add_argument('--fps', type=int, default=3)
    parser.add_argument('--wait', type=boolean, default=False)
    parser.add_argument('--episode', type=int, default=1)
    parser.add_argument('--memory_path', type=pathlib.Path, default="final_world/world_terr_ach/induction_from_reflexion_CC/202405302001-gpt-4-0125-preview")
    
    parser.add_argument('--gen_world', type=boolean, default=False)
    parser.add_argument('--revive', type=boolean, default=False)

    args = parser.parse_args()

    pygame.init()
    screen = pygame.display.set_mode(args.window)
    clock = pygame.time.Clock()

    record_path = args.load_world / args.model
    

    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    log_filename = f"{timestamp}-{MODEl}"
    all_path = record_path / log_filename
    all_path.mkdir(parents=True, exist_ok=True)


    current_file_abs = os.path.abspath(__file__)
    code_file = record_path / log_filename / os.path.basename(__file__)
    shutil.copyfile(current_file_abs, code_file)

    env = mars.Env(seed= args.seed, args = args, screen=screen, clock=clock, length=1000)
    env = mars.Recorder(env, record_path / log_filename)

    logger = setup_logger(record_path / log_filename / "logger.txt")

    bot = AgentController(env)
    env_wrap = envWrapper(env)
    
    controller_reflector = LLMcontrollerReflector(induced_path= args.memory_path / "reflection.txt", path = all_path, logger=logger)
    task_selector = Task_Selector(controller_reflector = controller_reflector, logger=logger)
    task_plan = Task_Planner(controller_reflector = controller_reflector, logger=logger)
    reflector = Reflector(controller_reflector = controller_reflector, logger=logger)
    descriptor = Descriptor(logger=logger)
    
    controller = LLMcontroller(controller_reflector = controller_reflector, env=env, logger=logger)
    trial_limit = 3
    task_action_seq = dict()
    task_completed = set()
    task_failed =set()
    memory = dict()
    memory = load_json(args.memory_path / 'memory.json')
    for episode in range(args.episode):

        logger.info("="*20 + f" trial {episode} " + "="*20)
        
        # initialize the env and get obs
        env.reset()
        obs, reward, done, info = env.step(0)
        done = False
        task_completed = set()
        task_failed = set()
        while not done:
            description = task_selector.render_human_message(env_wrap, task_completed, task_failed)
            # logger.info("=="*10 + "\nDescription: " + description + '\n' + "=="*10 )
            next_task = task_selector(description)
            while True:
                
                if next_task.replace(' ', '_') not in env.info['achievements']:
                    # query again
                    next_task = task_selector.task_error(description)
                    
                else:
                    break
            
            achievements_temper = copy.deepcopy(env.info['achievements'])
            

            if next_task.replace(' ', '_') not in memory:
                memory[next_task.replace(' ', '_')] = list()


            # description = task_plan.render_human_message(env_wrap)
            dialogue = descriptor(env.info)
            action_seq, dialogue = task_plan(dialogue, next_task, memory[next_task.replace(' ', '_')])
            
            

            for i in range(trial_limit):
                
                action_list = action_seq.split('\n')
                bot.reset()
                # current inventory
                cur_status = {k: v for k, v in env.info['inventory'].items() if k in VITALS}
                # cur_inventory = env.info['inventory']
                cur_inventory = {k: v for k, v in env.info['inventory'].items() if v > 0 and k not in VITALS}
                # table in view
                table_in_view = "table" in get_fov_types(env.info)
                furnace_in_view = "furnace" in get_fov_types(env.info)
                
                save_plan = list()

                for action in action_list:
                    reflection = ''

                    if 'step' in action:
                        if len(action.split(': ')) > 1:
                            action_exe = action.split(': ')[1]
                        else:
                            action_exe = action
                        # logger.info("=="*10 + "\nAction: " + action_exe + '\n' + "=="*10)
                        # exec(f"bot.{action_exe}")
                        before_achievement = copy.deepcopy(env.info['achievements'])
                        action_excute_res = controller(action_exe)
                        after_achievement = copy.deepcopy(env.info['achievements'])
                        logger.info("*"*20 + "all reward" + "*"*20)

                        logger.info(f"{env.info['all_reward']}")
                        save_plan.append(action_exe)
                        for k, v in after_achievement.items():
                            if after_achievement[k] - before_achievement[k] > 0:
                                achievement = k
                                plan_list = dict()
                                # plan_list['status'] = cur_status
                                plan_list["init_inventory"] = cur_inventory
                                plan_list["table_in_view"] = table_in_view
                                plan_list['furnace_in_view'] = furnace_in_view
                                plan_list['plan'] = save_plan
                                if achievement not in memory:
                                    memory[achievement] = list()
                                if plan_list not in memory[achievement]:
                                    memory[achievement].append(plan_list)
                                save_json(all_path / 'memory.json', memory)
                                    
                        # except Exception as e:
                        #     print(e)
                        #     action_status = 'invalid'
                        #     break
                        # else:
                            # observation = task_plan.render_human_message(env_wrap)
                            # logger.info("=="*10 + "\nObservation: " + observation + '\n'+ "=="*10)
                            # task_action_seq[next_task].append(action)
                        if env.info['done']:
                            break
                        
                        if action_excute_res == True:
                            action_status = "success"
                        elif action_excute_res == False:
                            action_status = "failed"
                        elif action_excute_res == "TIMEOUT":
                            action_status = "timeout"
                        # action_status = env.info['task_complete']
                    
                    
                        if action_status != "success":
                            dialogue += descriptor(env.info, action, action_status)
                            reflection, dialogue = reflector.reflect_plan(memory[next_task.replace(' ', '_')],dialogue)
                            break
                    
                # if the task is completed
                task_str = next_task.replace(' ', '_')
                if (env.info['achievements'][task_str] - achievements_temper[task_str]) > 0:
                    # # successful plan save to memory
                    # plan_list = dict()
                    # # plan_list['status'] = cur_status
                    # plan_list["init_inventory"] = cur_inventory
                    # plan_list["table_in_view"] = table_in_view
                    # plan_list['furnace_in_view'] = furnace_in_view
                    # plan_list['plan'] = save_plan
                    # if plan_list not in memory[next_task.replace(' ', '_')]:
                    #     memory[next_task.replace(' ', '_')].append(plan_list)
                    # save_json(all_path / 'memory.json', memory)

                    break

                elif i < trial_limit - 1:
                    if reflection == '':
                        dialogue += descriptor.plan_error(next_task)
                        reflection, dialogue = reflector.reflect_plan(memory[next_task.replace(' ', '_')],dialogue)
                        action_seq, dialogue = task_plan.replan(next_task,memory=memory[next_task.replace(' ', '_')], history=dialogue)
                    else:
                        # if action_status == "timeout":
                        #     dialogue += descriptor(env.info, action, action_status)
                        #     reflection, dialogue = reflector.reflect_plan(dialogue)
                        action_seq, dialogue = task_plan.replan(next_task, memory=memory[next_task.replace(' ', '_')], history=dialogue)

                    # if "OVER" in action_seq:
                    #     break
                if env.info['done']:
                    break
            # select achievement has been completed
            task_completed = set([k.replace('_', ' ') for k, v in env.info['achievements'].items() if v > 0])

            
            if env.info['achievements'][task_str] == 0:
                task_failed.add(next_task)

            for k, v in env.info['achievements'].items():
                if v > 0:
                    if k.replace('_', ' ') in task_failed:
                        task_failed.remove(k.replace('_', ' '))
            if env.info['done']:
                break
        
        save_inductive_memory(all_path, episode, controller_reflector.memory)
    pygame.quit()
    

if __name__ == "__main__":
    main()

