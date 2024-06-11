

from openai import AzureOpenAI
from utils import *
from mars.api.envWrapper import *
from mars.api.controller import *
import argparse
import pathlib

import pygame
import mars, os, shutil

from datetime import datetime
REGION = "" 
# MODEL = "gpt-35-turbo-0125"
MODEl = "gpt-4-0125-preview"


API_KEY = ""

API_BASE = "" 
ENDPOINT = f"{API_BASE}/{REGION}"

llm = AzureOpenAI(
    api_key=API_KEY,
    api_version="2024-02-01",
    azure_endpoint=ENDPOINT,
    )

def llm_invoke(system_message, human_message ) -> str:
    trial = 0
    while trial < 30:
        try:
            response = llm.chat.completions.create( 
                model=MODEl,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": human_message}
                ],
                temperature=0.5,
                stop='\n'
            )
        except:
            trial += 1
            continue
        else:
            break

    return response.choices[0].message.content



def render_system_message() -> str:
    import prompt
    system_template = prompt.sys_msg
    # system_template = load_prompt('baselines/ReAct_CC_std_situated/system_prompt_2.txt')
    with open('final_world/world_ach/world_rules.txt', 'r') as f:
        rule = f.read()
    system_msg = system_template.format(rules=rule)
    # programs = load_text('baselines/ReAct/programs.txt')
    return system_msg

def render_human_message(info) -> str:

    try:
        result = ""
        
        # if action is not None:
        #     result+=describe_act(info)
        result = decribe_player_walk(info)
        result += describe_status(info)
        result += describe_env_change(info)
        # result += "\n"

        result += describe_inventory(info)
        
        return result.strip()
    except:
        return "Error, you are out of the map."


# main function
def main():
    boolean = lambda x: bool(['False', 'True'].index(x))
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=530)
    parser.add_argument('--area', nargs=2, type=int, default=(64, 64))
    parser.add_argument('--view', type=int, nargs=2, default=(9, 9))
    parser.add_argument('--length', type=int, default=1000)
    parser.add_argument('--health', type=int, default=9)
    parser.add_argument('--window', type=int, nargs=2, default=(600, 600))
    parser.add_argument('--size', type=int, nargs=2, default=(0, 0))
    parser.add_argument('--load_world', type=pathlib.Path, default="final_world/world_ach")
    parser.add_argument('--model', type=str, default="ReAct_final_situated_CC")
    parser.add_argument('--fps', type=int, default=3)
    parser.add_argument('--wait', type=boolean, default=False)
    parser.add_argument('--gen_world', type=boolean, default=False)
    parser.add_argument('--revive', type=boolean, default=True)
    parser.add_argument('--episode', type=int, default=2)

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

    for i in range(args.episode):
        logger.info("="*20 + f" trial {i} " + "="*20)
        env.reset()
        obs, reward, done, info = env.step(0)
        # bot = AgentController(env)
        # env_wrap = envWrapper(env)

        done = False
        R = 0
        trajectories = []
        step = 0
        system_message = render_system_message()
        human_message = render_human_message(info)
        trajectories.append((step, human_message, ''))

        logger.info(system_message)
        logger.info(human_message)
        while not done:
            response = llm_invoke(system_message, human_message)
            logger.info(response)
            if response:
                if response.startswith('ACTION: '):
                    action = response.split(': ')[1]
                    try:
                        # exec(action)
                        obs, reward, done, info = env.step(ACTIONS_NAME.index(action))
                    except Exception as e:
                        print(e)
                        observation = "The generated action is not valid. Please check the available actions."
                    else:
                        observation = render_human_message(info)
                    R += env.info['reward']
                    done = env.info['done']
                    logger.info("Reward: %f" % R)
                    logger.info("Score: %f" % env.info['score'])
                    # trajectories.append((step, response, observation))
                    

                elif response.startswith('THINK: '):
                    observation = "OK."
                    # trajectories.append((step, response, observation))

                else:
                    observation = "The output is not valid. Please check the output format."
            else:
                observation = "You output 'None'. Please regenerate the output."
            
            step += 1
            trajectories.append((step, response, observation))
            human_message = "".join([f"{c}\n{d}\n" for i, c, d in trajectories[-10:]])
            logger.info(observation)
            if done:
                break
            # if step > 5000:
            #     env._save()
            #     break
        
    pygame.quit()

if __name__ == "__main__":
    main()

