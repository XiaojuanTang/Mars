import numpy as np
from mars.api.envWrapper import *
import mars
import logging

id_to_item = ID2OBJ
world_object = WORLD_OBJECT


def setup_logger(log_file='logfile.log'):
    # 设置日志格式，不包含时间
    log_formatter = logging.Formatter("%(message)s")

    # 创建 logger
    logger = logging.getLogger("my_logger")
    logger.setLevel(logging.INFO)

    # 将日志输出到文件
    log_file_handler = logging.FileHandler(log_file)
    log_file_handler.setFormatter(log_formatter)
    logger.addHandler(log_file_handler)

    # 将日志输出到控制台（屏幕）
    log_stream_handler = logging.StreamHandler()
    log_stream_handler.setFormatter(log_formatter)
    logger.addHandler(log_stream_handler)

    return logger



def load_text(fpaths, by_lines=False):
    with open(fpaths, "r") as fp:
        if by_lines:
            return fp.readlines()
        else:
            return fp.read()
        
def load_prompt(prompt):
    # package_path = pkg_resources.resource_filename("ReAct", "")
    return load_text(prompt)

def decribe_player_walk(info):
    player_walk_in = info['walk_in']
    return f"You are on the {player_walk_in}.\n"

def describe_env(info):

    player_idx = OBJ2ID['player']
    assert(info['semantic'][info['player_pos'][0],info['player_pos'][1]] == player_idx)
    # semantic = info['semantic'][info['player_pos'][0]-info['view'][0]//2:info['player_pos'][0]+info['view'][0]//2+1, info['player_pos'][1]-info['view'][1]//2+1:info['player_pos'][1]+info['view'][1]//2]
    semantic = get_fov(info)
    
    center = np.array([info['view'][0]//2,info['view'][1]//2-1])
    result = "You see: (object with coordinate)\n"
    x = np.arange(semantic.shape[1])
    y = np.arange(semantic.shape[0])
    x1, y1 = np.meshgrid(x,y)
    loc = np.stack((y1, x1),axis=-1)
    dist = np.absolute(center-loc).sum(axis=-1)
    obj_info_list = []
    
    all_dir = list(MOVE_LIST.values())
    facing = info['player_facing']
    result += '<'
    # result += "Nearby Blocks: \n"
    record_blocks = set()
    for dir in all_dir:
        target = (center[0] + dir[0], center[1] + dir[1])
        target = id_to_item[semantic[target]]
        record_blocks.add(target)
        if dir == facing:
            obs = f"{target}{(dir[0],-dir[1])} [also in your front], "
            # obs = "- {} 1 step at your {} (front).\n".format(target, self.describe_loc(np.array([0,0]),facing))
        else:
            obs = f"{target}{(dir[0],-dir[1])}, "
            # obs = "- {} 1 step at your {}.\n".format(target, self.describe_loc(np.array([0,0]),dir))
        result += obs 
    

    

    # result += 'Other Blocks: \n'

    for idx in np.unique(semantic):
        if idx==player_idx:
            continue
        if id_to_item[idx] in record_blocks:
            continue
        smallest = np.unravel_index(np.argmin(np.where(semantic==idx, dist, np.inf)), semantic.shape)
        obj_info_list.append((id_to_item[idx], dist[smallest], tuple(smallest-center)))

    if len(obj_info_list)>0:
        # status_str = "You see:\n{}".format("\n".join(["- nearest {} {} steps to your {}".format(name, dist, loc) for name, dist, loc in obj_info_list]))
        status_str = f", ".join([f"{name}{(cor[0],-cor[1])}" for name, dist, cor in obj_info_list])
        # status_str = "{}".format("\n".join(["- nearest {} {} steps to your {}".format(name, dist, loc) for name, dist, loc in obj_info_list]))
    else:
        # status_str = "You see nothing away from you."
        status_str = ""
        result = result[:-2]

    
    result += status_str + ">\n\n"
    # result += obs.strip()
    

    

    return result



def describe_env_change(info):

    player_idx = OBJ2ID['player']
    assert(info['semantic'][info['player_pos'][0],info['player_pos'][1]] == player_idx)
    # semantic = info['semantic'][info['player_pos'][0]-info['view'][0]//2:info['player_pos'][0]+info['view'][0]//2+1, info['player_pos'][1]-info['view'][1]//2+1:info['player_pos'][1]+info['view'][1]//2]
    semantic = get_fov(info)
    center = np.array([info['view'][0]//2,info['view'][1]//2-1])
    result = "You see: (object with coordinate)\n"
    x = np.arange(semantic.shape[1])
    y = np.arange(semantic.shape[0])
    x1, y1 = np.meshgrid(x,y)
    loc = np.stack((y1, x1),axis=-1)
    dist = np.absolute(center-loc).sum(axis=-1)
    obj_info_list = []
    
    all_dir = list(MOVE_LIST.values())
    facing = info['player_facing']
    
    # result += "Nearby Blocks: \n"
    record_blocks = set()
    block_kind = set()

    facing_block = ''
    adj_str = ''
    for dir in all_dir:
        target = (center[0] + dir[0], center[1] + dir[1])
        target = id_to_item[semantic[target[0], target[1]]]
        record_blocks.add((target, 1, (dir[0], dir[1])))
        block_kind.add(target)
        if dir == facing:
            obs = f"{target}{(dir[0],-dir[1])}, "
            facing_block = f"{target} is in front of you.\n"
            # obs = "- {} 1 step at your {} (front).\n".format(target, self.describe_loc(np.array([0,0]),facing))
        else:
            obs = f"{target}{(dir[0],-dir[1])}, "
            # obs = "- {} 1 step at your {}.\n".format(target, self.describe_loc(np.array([0,0]),dir))
        adj_str += obs 
    result += facing_block
    result += '<' + adj_str
    # result += 'Other Blocks: \n'

    for idx in np.unique(semantic):
        if idx==player_idx:
            continue
        if id_to_item[idx] in block_kind:
            continue
        smallest = np.unravel_index(np.argmin(np.where(semantic==idx, dist, np.inf)), semantic.shape)
        obj_info_list.append((id_to_item[idx], dist[smallest], tuple(smallest-center)))
        record_blocks.add((id_to_item[idx], dist[smallest], tuple(smallest-center)))
    
    for i in loc:
        for j in i:
            tgt = id_to_item[semantic[j[0], j[1]]]
            if tgt in world_object:
                record = (tgt, np.absolute(center-j).sum(), tuple(j-center))
                if record not in record_blocks:
                    record_blocks.add(record)
                    obj_info_list.append(record)

    if len(obj_info_list)>0:
        # status_str = "You see:\n{}".format("\n".join(["- nearest {} {} steps to your {}".format(name, dist, loc) for name, dist, loc in obj_info_list]))
        status_str = f", ".join([f"{name}{(cor[0],-cor[1])}" for name, dist, cor in obj_info_list])
        # status_str = "{}".format("\n".join(["- nearest {} {} steps to your {}".format(name, dist, loc) for name, dist, loc in obj_info_list]))
    else:
        # status_str = "You see nothing away from you."
        status_str = ""
        result = result[:-2]

    
    result += status_str + ">\n"
    # result += obs.strip()
    return result



def describe_inventory(info):
    
    result = ""
    
    status_str = "Your status: <{}>".format(", ".join(["{}: {}/9".format(v, info['inventory'][v]) for v in VITALS]))
    result += status_str + "\n"
    
    inventory_str = ", ".join(["{}: {}".format(i, num) for i,num in info['inventory'].items() if i not in VITALS and num!=0])
    inventory_str = "Your inventory: <{}>".format(inventory_str) if inventory_str else "You have nothing in your inventory."
    result += inventory_str #+ "\n\n"
    
    return result

def describe_status(info):
    
    if info['sleeping']:
        return "You are sleeping, and will not be able take actions until energy is full.\n"
    elif info['dead']:
        return "You died.\n"
    else:
        return ""



def describe_env_all(info):

    player_idx = OBJ2ID['player']
    assert(info['semantic'][info['player_pos'][0],info['player_pos'][1]] == player_idx)
    # semantic = info['semantic'][info['player_pos'][0]-info['view'][0]//2:info['player_pos'][0]+info['view'][0]//2+1, info['player_pos'][1]-info['view'][1]//2+1:info['player_pos'][1]+info['view'][1]//2]
    semantic = get_fov(info)
    center = np.array([info['view'][0]//2,info['view'][1]//2-1])
    result = "You see: (object with coordinate)\n"
    x = np.arange(semantic.shape[1])
    y = np.arange(semantic.shape[0])
    x1, y1 = np.meshgrid(x,y)
    loc = np.stack((y1, x1),axis=-1)
    dist = np.absolute(center-loc).sum(axis=-1)
    obj_info_list = []
    
    all_dir = list(MOVE_LIST.values())
    facing = info['player_facing']
    
    # result += "Nearby Blocks: \n"
    record_blocks = set()
    block_kind = set()
    facing_block = ''

    adj_str = ''
    for dir in all_dir:
        target = (center[0] + dir[0], center[1] + dir[1])
        target = id_to_item[semantic[target[0], target[1]]]
        record_blocks.add((target, 1, (dir[0], dir[1])))
        block_kind.add(target)
        if dir == facing:
            facing_block = f"You are facing {target}{(dir[0], -dir[1])}.\n"
            # obs = f"{target}{(dir[0],-dir[1])} [also in my front], "
            # obs = "- {} 1 step at your {} (front).\n".format(target, self.describe_loc(np.array([0,0]),facing))
        else:
            obs = f"{target}{(dir[0],-dir[1])}, "
            # obs = "- {} 1 step at your {}.\n".format(target, self.describe_loc(np.array([0,0]),dir))
            adj_str += obs 
    result += facing_block
    result += 'Other blocks: <' + adj_str
    # result += 'Other Blocks: \n'

    # for idx in np.unique(semantic):
    #     if idx==player_idx:
    #         continue
    #     if id_to_item[idx] in block_kind:
    #         continue
    #     smallest = np.unravel_index(np.argmin(np.where(semantic==idx, dist, np.inf)), semantic.shape)
    #     obj_info_list.append((id_to_item[idx], dist[smallest], tuple(smallest-center)))
    #     record_blocks.add((id_to_item[idx], dist[smallest], tuple(smallest-center)))
    
    for i in loc:
        for j in i:
            if semantic[j[0], j[1]] == player_idx:
                continue
            tgt = id_to_item[semantic[j[0], j[1]]]
            # if tgt in world_object:
            record = (tgt, np.absolute(center-j).sum(), tuple(j-center))
            if record not in record_blocks:
                record_blocks.add(record)
                obj_info_list.append(record)

    obj_info_list = sorted(obj_info_list, key=lambda x: x[1])

    if len(obj_info_list)>0:
        # status_str = "You see:\n{}".format("\n".join(["- nearest {} {} steps to your {}".format(name, dist, loc) for name, dist, loc in obj_info_list]))
        status_str = f", ".join([f"{name}{(cor[0],-cor[1])}" for name, dist, cor in obj_info_list])
        # status_str = "{}".format("\n".join(["- nearest {} {} steps to your {}".format(name, dist, loc) for name, dist, loc in obj_info_list]))
    else:
        # status_str = "You see nothing away from you."
        status_str = ""
        result = result[:-2]

    
    result += status_str + ">\n"
    # result += obs.strip()
    return result




def get_fov(info):
    '''
    Get the player's field of view.
    '''
    pos = info['player_pos']
    obs = info['semantic']

    fov_size = np.array([9, 7])
    top_left = np.maximum(pos - fov_size // 2, 0)
    bottom_right = np.minimum(pos + fov_size // 2 + 1, obs.shape)
    fov = obs[top_left[0]:bottom_right[0], top_left[1]:bottom_right[1]]
    pad_top = top_left[0] - pos[0] + fov_size[0] // 2
    pad_bottom = pos[0] + fov_size[0] // 2 + 1 - bottom_right[0]
    pad_left = top_left[1] - pos[1] + fov_size[1] // 2
    pad_right = pos[1] + fov_size[1] // 2 + 1 - bottom_right[1]
    fov = np.pad(fov, ((pad_top, pad_bottom), (pad_left, pad_right)), mode='constant', constant_values=0)
    return fov


def describe_reward_score(info):
    score = info['score']
    reward = info['all_reward']

    result = f"Currrently, your reward is {reward}, and your score is {score}.\n\n"

    return result