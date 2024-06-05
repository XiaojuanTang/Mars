

from openai import AzureOpenAI
from utils import *
from crafter.api.envWrapper import *
from crafter.api.controller import *
import argparse
import pathlib
from openai import OpenAI
import pygame
import crafter, os, shutil
import tiktoken
from datetime import datetime
REGION = "" 
# MODEL = "gpt-35-turbo-0125"
MODEl = "gpt-4-0125-preview"

API_KEY = ""
API_BASE = "" 
ENDPOINT = f"{API_BASE}/{REGION}"

enc = tiktoken.encoding_for_model("text-davinci-003")

llm = AzureOpenAI(
    api_key=API_KEY,
    api_version="2024-02-01",
    azure_endpoint=ENDPOINT,
    )

def llm_invoke(system_message, human_message, stop=None ) -> str:
    trial = 0
    while trial < 20:
        try:
            response = llm.chat.completions.create( 
                model=MODEl,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": human_message}
                ],
                temperature=0.5,
                stop=stop
            )
        except:
            trial += 1
            continue
        else:
            break


    return response.choices[0].message.content

def render_system_message() -> str:
        
    system_template = load_prompt('baselines/reflexion_std_CC/system_prompt.txt')
    
    # programs = load_text('baselines/ReAct/programs.txt')
    return system_template

def render_human_message(info) -> str:

    try:
        result = ""
        
        # if action is not None:
        #     result+=describe_act(info)
        result = describe_reward_score(info)
        result += decribe_player_walk(info)
        result += describe_status(info)
        result += describe_env_change(info)
        # result += "\n"

        result += describe_inventory(info)
        
        return result.strip()
    except:
        return "Error, you are out of the map."

def reflect(experience, reward_deta, score_deta):
    system_message = load_prompt('baselines/reflexion_std_CC/reflexion_sys_prompt.txt')
    user_message = load_prompt('baselines/reflexion_std_CC/reflexion_user_prompt.txt')
    user_message = user_message.format(experience=experience, reward_deta=reward_deta, score_deta=score_deta)
    response = llm_invoke(system_message, user_message)
    return response

# main function
def main():
    boolean = lambda x: bool(['False', 'True'].index(x))
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=529)
    parser.add_argument('--area', nargs=2, type=int, default=(64, 64))
    parser.add_argument('--view', type=int, nargs=2, default=(9, 9))
    parser.add_argument('--length', type=int, default=None)
    parser.add_argument('--health', type=int, default=9)
    parser.add_argument('--window', type=int, nargs=2, default=(600, 600))
    parser.add_argument('--size', type=int, nargs=2, default=(0, 0))
    parser.add_argument('--load_world', type=pathlib.Path, default="final_world/world_terr_ach")
    parser.add_argument('--model', type=str, default="Reflexion_v3_final")
    parser.add_argument('--fps', type=int, default=3)
    parser.add_argument('--wait', type=boolean, default=False)
    parser.add_argument('--death', type=str, default='reset', choices=[
        'continue', 'reset', 'quit'])
    parser.add_argument('--gen_world', type=boolean, default=False)
    parser.add_argument('--episode', type=int, default=4)
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

    env = crafter.Env(seed= args.seed, args = args, screen=screen, clock=clock)
    env = crafter.Recorder(env, record_path / log_filename)

    

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
        reward_seq = []
        score_seq = []
        step = 1
        system_message = render_system_message()
        human_message = render_human_message(info)
        history = ''
        trajectories.append((step, human_message, ''))
        history += human_message + '\n'
        reward_seq.append(env.info['all_reward'])
        score_seq.append(env.info['score'])
        logger.info(system_message)
        logger.info(human_message)
        # reflections = []
        while not done:
            response = llm_invoke(system_message, history, '\n')
            logger.info(response)
            if response:
                if response.startswith('ACTION: '):
                    action = response.split(': ')[1]
                    try:
                        # exec(action)
                        obs, reward, done, info = env.step(ACTIONS_NAME.index(action))
                    except:
                        observation = "The generated action is not valid. Please check the available actions."
                    else:
                        observation = render_human_message(info)
                    R += env.info['reward']
                    done = env.info['done']
                    # trajectories.append((step, response, observation))
                    

                elif response.startswith('THINK: '):
                    observation = "OK."
                    # trajectories.append((step, response, observation))

                else:
                    observation = "The output is not recognized."
            else:
                observation = "You output 'None'."
            logger.info(observation)


            step += 1

            trajectories.append((step, response, observation))
            history += f"{response}\n{observation}\n"
            score_seq.append(env.info['score'])
            reward_seq.append(env.info['all_reward'])
            # human_message = "".join([f"{c}\n{d}\n" for i, c, d in trajectories[-10:]])

            # perform reflection
            if len(enc.encode(history)) > 3896:
            # if step >= 10 and step % 10 == 0:
                # reflection
                # history = "".join([f"{c}\n{d}\n" for i, c, d in trajectories[-10:]])
                reward_deta = reward_seq[-1] - reward_seq[0]
                score_deta = score_seq[-1] - score_seq[-0]
                reflection = reflect(history, reward_deta, score_deta)
                # reflection_str = f"THINK: {reflection.split('REFLECTION: ')[1]}"
                logger.info(reflection)
                # trajectories.remove((step, response, observation))
                # reflections.append(reflection_str)
                observation += '\n' + reflection
                # trajectories.append((step, response, observation))

                trajectories = [(step, '', observation)]
                history = observation + '\n'
                reward_seq = [reward_seq[-1]]
                score_seq = [score_seq[-1]]
                

            # human_message = "".join([f"{c}\n{d}\n" for i, c, d in trajectories[-10:]])
            if done:
                break
            # if step > 5000:
            #     env._save()
            #     break
    
    pygame.quit()

if __name__ == "__main__":
    main()

