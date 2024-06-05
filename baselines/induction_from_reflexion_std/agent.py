
from typing import Any
from openai import AzureOpenAI
from utils import *
from prompt import *
from openai import OpenAI



class AnyOpenAILLM:
    def __init__(self, model_name = MODEl, temperature=0.5, sys_msg=None):
        self.model_name = model_name
        self.temperature = temperature
        self.message = [{"role": "system", "content": sys_msg}]
        self.client = AzureOpenAI(
                    api_key=API_KEY,
                    api_version="2024-02-01",
                    azure_endpoint=ENDPOINT,
                    )
        

    def __call__(self, user_msg: list):
        
        message = self.message + user_msg
        
        response = None
        while not response:
            
            msg = self.client1.chat.completions.create(
                model=self.model_name,
                messages=message,
                temperature=self.temperature,
            )
            
            response = msg.choices[0].message.content
            
        return response

    





    

    # def render_user_message(self, msg: str):
    #     return [{"role": "user", "content": msg}]

    # def render_assistant_message(self, msg: str):
    #     return [{"role": "assistant", "content": msg}]
    

class Task_Selector:
    def __init__(self, controller_reflector, model_name = MODEl, temperature=0.5, sys_msg=None, logger=None):
        sys_msg = TASK_SELECTOR_SYS
        self.llm = AnyOpenAILLM(model_name, temperature, sys_msg)
        self.logger = logger
        self.controller_reflector = controller_reflector
        

    def __call__(self, msg: str):
        
        user_msg = [{"role": "user", "content": msg}]
        self.logger.info("="*20 + "User" + "="*20)
        self.logger.info(msg)
        if len(self.controller_reflector.memory) > 0:
            memory_str = REFLECTION_MEMORY_ASSISTANT.format(memory = self.controller_reflector.memory)
            user_msg += [{"role": "assistant", "content": memory_str}]
        
        response = self.llm(user_msg)
        self.logger.info("="*20 + "Task Selector" + "="*20)
        self.logger.info(response)
        return self.parse_ai_message(response)
    
    def task_error(self, msg):
        result =  "I select a task that does not exist in the task pool."
        user_msg = [{"role": "user", "content": msg}]

        user_msg += [{"role": "assistant", "content": result}]
        self.logger.info("="*20 + "User" + "="*20)
        self.logger.info(result)
        response = self.llm(user_msg)
        self.logger.info("="*20 + "Task Selector" + "="*20)
        self.logger.info(response)
        return self.parse_ai_message(response)

    
    def parse_ai_message(self, message):
        task = ""
        for line in message.split("\n"):
            if line.startswith("Task:"):
                task = line[5:].replace(".", "").strip()
        assert task, "Task not found in Curriculum Agent response"
        return task
    
    def render_human_message(self, env_wrap, task_complete, task_failed):
        info = env_wrap._env.info
        try:
            result = ""
            
            # if action is not None:
            #     result+=describe_act(info)
            # result = describe_action_result(info)
            # result += describe_reward_score(score_deta, reward_deta)
            result += describe_player_walk(info)
            result += describe_status(info)
            result += describe_env_change(info)
            # result += "\n"

            result += describe_inventory(info)

            # describe_task_complete 
            task_complete_str = ', '.join(task_complete)
            task_failed_str = ', '.join(task_failed)
            result += f"Completed tasks so far: {task_complete_str}\n"
            result += f"Failed tasks: {task_failed_str}\n"
            return result.strip()
        except:
            return "Error, you are out of the map."
    

class Task_Planner:

    def __init__(self, controller_reflector, model_name = MODEl, temperature=0.5, sys_msg=None, logger=None, **kwargs):
        sys_msg = TASK_PLANNER_SYS
        self.llm = AnyOpenAILLM(model_name, temperature, sys_msg)
        # self.llm.message += [{"role": "user", "content": TASK_PLANNER_USER_1}]
        # self.llm.message += [{"role": "assistant", "content": TASK_PLANNER_ASSIST_1}]
        # self.llm.message += [{"role": "user", "content": TASK_PLANNER_USER_2}]
        # self.llm.message += [{"role": "assistant", "content": TASK_PLANNER_ASSIST_2}]
        self.logger = logger
        self.controller_reflector = controller_reflector
        
        
    def __call__(self, user_msg: list, task_msg: str, memory: dict ={}, reflection_memory: list = []):
        prompt_msg = TASK_PLANNER_USER_TEMPLATE.format(task=task_msg)
        self.logger.info("="*20 + "User" + "="*20)
        self.logger.info(prompt_msg)
        memory_list = []
        if len(memory) > 0:
            memory_str = TASK_MEMORY_ASSISTANT.format(memory = memory)
            memory_list += [{"role": "assistant", "content": memory_str}]
        if len(self.controller_reflector.memory) > 0:
            memory_str = REFLECTION_MEMORY_ASSISTANT.format(memory = self.controller_reflector.memory)
            memory_list += [{"role": "assistant", "content": memory_str}]
        user_msg += [{"role": "user", "content": prompt_msg}]
        
        response = self.llm(memory_list + user_msg)
        self.logger.info("="*20 + "Task Planner" + "="*20)
        self.logger.info(response)
        msg = user_msg + [{"role": "assistant", "content": f"[Plan]{response}"}]
        return response, msg

    def replan(self, task_msg: str, memory: dict = {}, history: list=[]):
        user_msg_list = []
        user_msg = TASK_REPLANNER_USER.format(task=task_msg)
        self.logger.info("="*20 + "User" + "="*20)
        self.logger.info(user_msg)
        user_msg = [{"role": "user", "content": user_msg}]
        if len(memory) > 0:
            memory_str = TASK_MEMORY_ASSISTANT.format(memory = memory)
            user_msg_list += [{"role": "assistant", "content": memory_str}]
        if len(self.controller_reflector.memory) > 0:
            memory_str = REFLECTION_MEMORY_ASSISTANT.format(memory = self.controller_reflector.memory)
            user_msg_list += [{"role": "assistant", "content": memory_str}]
        
        response = self.llm(user_msg_list + history + user_msg)
        self.logger.info("="*20 + "Task RePlanner" + "="*20)
        self.logger.info(response)
        msg = user_msg + [{"role": "assistant", "content": f"[RePlan] {response}"}]
        return response, history + msg
    
    def parse_ai_message(self, messge):
        pass

        
    def render_human_message(self, env_wrap, start=True):
        info = env_wrap._env.info
        try:
            result = ""
            
            # if action is not None:
            #     result+=describe_act(info)
            if not start:
                result += describe_action_result(info)
            # result += describe_reward_score(score_deta, reward_deta)
            result += describe_player_walk(info)
            result += describe_status(info)
            result += describe_env_change(info)
            # result += "\n"

            result += describe_inventory(info)

            # # describe_task_complete 
            # task_complete_str = ', '.join(task_complete)
            # task_failed_str = ', '.join(task_failed)
            # result += f"Completed tasks so far: {task_complete_str}\n"
            # result += f"Failed tasks that are too hard: {task_failed_str}\n"
            return result.strip()
        except:
            return "Error, you are out of the map."
    

    def load_memory(self):
        pass

class Reflector(AnyOpenAILLM):
    def __init__(self, controller_reflector, model_name = MODEl, temperature=0.5, sys_msg=None, logger=None, **kwargs):
        sys_msg = REFLECTION_SYS
        self.llm = AnyOpenAILLM(model_name, temperature, sys_msg)
        # self.llm.message += [{"role": "user", "content": REFLECTION_USER_1}]
        # self.llm.message += [{"role": "assistant", "content": REFLECTION_ASSIST_1}]
        # self.llm.message += [{"role": "user", "content": REFLECTION_USER_2}]
        # self.llm.message += [{"role": "assistant", "content": REFLECTION_ASSIST_2}]
        # # self.llm.message += [{"role": "user", "content": REFLECTION_USER_3}]
        # # self.llm.message += [{"role": "assistant", "content": REFLECTION_ASSIST_3}]
        # self.llm.message += [{"role": "user", "content": REFLECTION_USER_4}]
        # self.llm.message += [{"role": "assistant", "content": REFLECTION_ASSIST_4}]
        self.logger = logger
        self.controller_reflector = controller_reflector

    def reflect_plan(self, memory,  user_msg: list):
        # user_msg = REFLECTION_USER_TEMPLATE.format(action = action_msg, description = description)
        # user_msg = [{"role": "user", "content": user_msg}]
        user_msg_list = []
        if len(memory) > 0:
            memory_str = TASK_MEMORY_ASSISTANT.format(memory = memory)
            user_msg_list += [{"role": "assistant", "content": memory_str}]
        if len(self.controller_reflector.memory) > 0:
            memory_str = REFLECTION_MEMORY_ASSISTANT.format(memory = self.controller_reflector.memory)
            user_msg_list += [{"role": "assistant", "content": memory_str}]
        
        response = self.llm(user_msg_list + user_msg)
        user_msg += [{"role": "assistant", "content": f"[Reflection] {response}"}]
        self.logger.info("="*20 + "Reflector" + "="*20)
        self.logger.info(response)
        
        return response, user_msg
    
    # def reflect_plan(self, memory, user_msg: list) -> Any:
    #     # user_msg = [{"role": "user", "content": user_msg}]
    #     # history += user_msg
    #     user_msg_list = []
    #     if len(memory) > 0:
    #         memory_str = TASK_MEMORY_ASSISTANT.format(memory = memory)
    #         user_msg_list += [{"role": "assistant", "content": memory_str}]
       
    #     response = self.llm(user_msg)
    #     self.logger.info("="*20 + "Reflector" + "="*20)
    #     self.logger.info(response)
        
    #     user_msg += [{"role": "assistant", "content": f"[Reflection] {response}"}]
    #     return response, user_msg
    

class Descriptor:
    def __init__(self, logger=None):
        self.logger = logger

    def __call__(self, info: dict, action_str=None, action_status=None):

        result_string = ''
        if action_str:

            if action_status == "timeout":
                result_string += f"I failed on {action_str} because of timeout. Maybe I need to try again or I may make a mistake.\nCurrent observation: \n"
                # self.logger.info("="*20 + "Descriptor" + "="*20)
                # self.logger.info(result_string)
                
                # return [{"role": "user", "content": f"[Description] {result_string}"}]
            else:
                if action_status == 'success':
                    result_string += f"I succeed on {action_str}.\nCurrent observation: \n"

                else:
                    result_string += f"I failed on {action_str}.\nCurrent observation: \n"
                
        result_string += describe_player_walk(info)
        result_string += describe_status(info)
        result_string += describe_env_change(info)
        result_string += describe_inventory(info)
        self.logger.info("="*20 + "Descriptor" + "="*20)
        self.logger.info(result_string)
        return [{"role": "user", "content": f"[Description] {result_string}"}]
    
    def plan_error(self, task_msg: str):
        result_string = f"I succeed on all steps but failed to complete the task [{task_msg}].\n"
        self.logger.info("="*20 + "Descriptor" + "="*20)
        self.logger.info(result_string)
        return [{"role": "user", "content": f"[Description] {result_string}"}]
    def controller_des(self, info, subgoal_msg):
        result_string = ''
        if info['action'] is not None:
            result_string += describe_act(info)
        result_string += describe_player_walk(info)
        result_string += describe_status(info)
        result_string += describe_env_change(info)
        result_string += describe_inventory(info)
        # result_string += subgoal_msg
        self.logger.info("="*20 + "Descriptor" + "="*20)
        self.logger.info(result_string)
        return [{"role": "user", "content": f"[Description] {result_string}"}]


class LLMcontrollerReflector:
    def __init__(self, path, induced_path=None, model_name = MODEl, temperature=0.5, sys_msg=None, logger=None) -> None:
        
        self.logger = logger
        sys_msg = CONTROLLER_REFLECTION_SYS
        
        self.llm = AnyOpenAILLM(model_name, temperature, sys_msg)
        self.memory = set()
        self.mem_to_emb = dict()
        if induced_path:
            
            with open(induced_path, "r") as f:
                for line in f:
                    try:
                        # memory_each = line.split(":")[1].strip()
                        # self.add_memory_library(memory_each)
                        self.memory.add(line.split(":")[1].strip())
                    except:
                        pass
        # else:
        #     self.memory = set()
        # self.mem_to_emb = dict()
        self.path = path
        
    def __call__(self, history) -> Any:
        user_msg = '\n'.join(history)
        # if len(self.memory) > 0:
        #     memory_str = REFLECTION_MEMORY_ASSISTANT.format(memory = self.memory)
        #     user_msg = [{"role": "assistant", "content": memory_str}] + [{"role": "user", "content": user_msg}]
        # else:
        #     user_msg = [{"role": "user", "content": user_msg}]
        user_msg = [{"role": "user", "content": user_msg}]
        response = self.llm(user_msg)
        self.logger.info("="*20 + "Controller Reflector" + "="*20)
        self.logger.info(response)
        try:
            induced = response.split("Mechanism: ")[1]
            if len(induced.split("Action: ")) > 1:
                induced = induced.split("Action: ")[0].strip()
            if induced != "null":
                # self.memory.add(induced)
                self.add_memory_library(induced)
        except:
            pass
        self.save_memory()
    
    def save_memory(self):
        # list to string
        with open(self.path / "reflection.txt", "w") as f:
            id = 0
            for item in self.memory:
                f.write(f"{id}: {item}\n")
                id += 1
    
    def add_memory_library(self, induced):
        REGION = "canadaeast" 
        MODEL = "text-embedding-3-large"
        ENDPOINT = f"{API_BASE}/{REGION}"
        client = AzureOpenAI(api_key=API_KEY,
        api_version="2024-02-01",
        azure_endpoint=ENDPOINT,

        )
        # compute the similarity to add the memory
        induced_emb = client.embeddings.create(
            model=MODEL,
            input=induced
        ).data[0].embedding
        # compute similarity between the emb of induced and self.mem_to_emb
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        if len(self.memory) == 0:
            self.memory.add(induced)
            self.mem_to_emb[induced] = induced_emb
            return
        for key, value in self.mem_to_emb.items():
            sim = cosine_similarity(induced_emb, value)
            if sim > 0.8:
                # if len(value) < len(induced_emb):
                self.memory.remove(key)
                del self.mem_to_emb[key]

                self.memory.add(induced)
                self.mem_to_emb[induced] = induced_emb
                    
            else:
                self.memory.add(induced)
                self.mem_to_emb[induced] = induced_emb

        # return response



class LLMcontroller:

    def __init__(self, env, controller_reflector, induce = True, model_name = MODEl, temperature=0.5, sys_msg=None, logger=None) -> None:
        self.env = env
        self.logger = logger
        sys_msg = CONTROLLER_SYS
        
        self.llm = AnyOpenAILLM(model_name, temperature, sys_msg)
        self.controller_reflector = controller_reflector
        self.induce = induce
    def __call__(self, subgoal, timeout=10) -> Any:
        
        # reset the environment
        self.env.info['task_complete'] = 'failed'
        desciptor = Descriptor(self.logger)
        # get the user message
        user_template = CONTROLLER_USER_TEMPLATE.format(subgoal=subgoal)

        self.logger.info("="*20 + "User" + "="*20)
        self.logger.info(user_template)
        action_dialogue = []

        # # extract the amount
        # pattern = r"\w+\(['\"]?.+?['\"]?, (\d+)\)"
        # import re
        # match = re.findall(pattern, subgoal)
        # if len(match) > 0:
        #     amount = int(match[0])
        # else:
        #     amount = 1
        action_dialogue += [{"role": "user", "content": user_template}]
        if len(self.controller_reflector.memory) > 0:
            memory_str = REFLECTION_MEMORY_ASSISTANT.format(memory = self.controller_reflector.memory)
            action_dialogue += [{"role": "assistant", "content": memory_str}]
        timeout = 15
        history_to_induce = []
        self.env.info.update({"action": None})
        while timeout:
            # get the current observation
            desciption = desciptor.controller_des(self.env.info, user_template)
            # get the user message
            
            history_to_induce.append(desciption[-1]['content'])
            action_dialogue += desciption
            if len(action_dialogue) > 10:
                action_dialogue = [action_dialogue[0]] + action_dialogue[-10:]
            
            try:
                response = self.llm(action_dialogue)
                
                self.logger.info("="*20 + "Controller" + "="*20)
                self.logger.info(response)
                # get the action from the response
                action = response.split("Action: ")[1]
                # execute the action
                
                if action == "SUCCEED":
                    excute_res = True
                    break
                elif action == "FAILED":
                    excute_res = False
                    break
                else:
                    history_to_induce.append(f"Action: {action}")
                    self.env.step(ACTIONS_NAME.index(action))
                    if self.env.info['done']:
                        desciption = desciptor.controller_des(self.env.info, user_template)
                        history_to_induce.append(desciption[-1]['content'])
                        excute_res = False
                        break
            except Exception as e:
                self.logger.error(e)
                action_dialogue.append({"role": "assistant", "content": "The generated action is not valid. Please check the available actions."})
            else:
                action_dialogue.append({"role": "assistant", "content": response})
                
            # # check if the task is completed
            # if self.env.info['task_complete'] == 'success':
            #     amount -= 1
            # if amount == 0:
            #     break
            timeout -= 1
        if timeout == 0:
            excute_res = "TIMEOUT"
        
            desciption = desciptor.controller_des(self.env.info, user_template)
            history_to_induce.append(desciption[-1]['content'])
        # perform controller reflection
        if len(history_to_induce) > 1 and self.induce:
            self.controller_reflector(history_to_induce)
        return excute_res
            
            

