import basic
import time
from itertools import permutations
from collections import deque

COLS, ROWS = 5, 6


class Floor:
    def __init__(self, handle: basic.HANDLE):
        self.handle = handle
        self.grid_state = [[False for _ in range(COLS)] for _ in range(ROWS)]
        self.grid = basic.split_map_grid(handle)

    def _pos_to_coord(self, row, col):
        """将网格坐标转换为实际点击坐标"""
        for cell in self.grid:
            if cell[0] == row and cell[1] == col:
                x1, y1, x2, y2 = cell[2]
                return (
                    basic.back_to_before(self.handle, (x1 + x2) // 2),
                    basic.back_to_before(self.handle, (y1 + y2) // 2),
                )
        return None

    def find_door_pos(
        self, handle: basic.HANDLE, door_path="./img/common/locked_door.png"
    ):
        door_pos = basic.find_image_center(handle, [door_path])
        door_pos = (
            basic.resize_to_720(handle, door_pos[0][0]),
            basic.resize_to_720(handle, door_pos[0][1]),
        )
        for cell in self.grid:
            if door_pos[0] in range(cell[2][0], cell[2][2]) and door_pos[1] in range(
                cell[2][1], cell[2][3]
            ):
                return cell

    def find_monsters_pos(
        self,
        handle: basic.HANDLE,
        monsters=[
            "./img/monster/monster_block.png",
            "./img/monster/monster_1.png",
            "./img/monster/monster_2.png",
            "./img/monster/monster_3.png",
            "./img/monster/monster_4.png",
        ],
    ):
        monsters_pos = basic.find_image_centers(handle, monsters)

        cell_list = []
        for monster in monsters_pos:
            monster = (
                basic.resize_to_720(handle, monster[0]),
                basic.resize_to_720(handle, monster[1]),
            )
            for cell in self.grid:
                if monster[0] in range(cell[2][0], cell[2][2]) and monster[1] in range(
                    cell[2][1], cell[2][3]
                ):
                    cell_list.append(cell)
        return cell_list

    def find_obstacles_pos(
        self,
        handle: basic.HANDLE,
        obstacles=[
            "./img/obstacle/equipment_shop.png",
            "./img/obstacle/hole.png",
            "./img/obstacle/open_door.png",
            "./img/obstacle/wood.png",
        ],
    ):
        obstacles_pos = basic.find_image_centers(handle, obstacles)

        cell_list = []
        for obstacle in obstacles_pos:
            obstacle = (
                basic.resize_to_720(handle, obstacle[0]),
                basic.resize_to_720(handle, obstacle[1]),
            )
            for cell in self.grid:
                if obstacle[0] in range(cell[2][0], cell[2][2]) and obstacle[
                    1
                ] in range(cell[2][1], cell[2][3]):
                    cell_list.append(cell)
        return cell_list

    def find_shortest_path(self, start, target, obstacles):
        """从单个起点到单个目标点的最短路径（避开障碍物）"""
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        # 提取起点和目标点的坐标（row, col）
        start_row, start_col = start[0], start[1]
        target_row, target_col = target[0], target[1]
        # 提取障碍物的坐标（仅需要row, col）
        obstacle_coords = {
            (obs[0], obs[1]) for obs in obstacles
        }  # 转换为集合便于快速判断

        queue = deque([(start_row, start_col, [])])
        visited = set([(start_row, start_col)])

        while queue:
            row, col, path = queue.popleft()
            if row == target_row and col == target_col:
                return path + [(row, col)]  # 返回路径坐标（row, col）

            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                # 检查边界、未访问、非障碍物
                if (
                    0 <= new_row < ROWS
                    and 0 <= new_col < COLS
                    and (new_row, new_col) not in visited
                    and (new_row, new_col) not in obstacle_coords
                ):
                    visited.add((new_row, new_col))
                    queue.append((new_row, new_col, path + [(row, col)]))

        return None  # 未找到路径

    def find_shortest_path_through_all_targets(self, start, targets, obstacles):
        all_permutations = permutations(targets)
        shortest_path = None
        shortest_length = float("inf")

        for perm in all_permutations:
            current_path = []
            current_start = start
            for target in perm:
                path = self.find_shortest_path(current_start, target, obstacles)
                if path is None:
                    break
                if current_path:
                    current_path.extend(path[1:])
                else:
                    current_path.extend(path)
                current_start = target

            if len(current_path) < shortest_length:
                shortest_length = len(current_path)
                shortest_path = current_path

        return shortest_path

    def click_via_path(self, path):
        for cell in path[1:]:
            if cell[0] == start[0] and cell[1] == start[1]:
                continue
            if cell[0] == 5 and cell[1] == 0:
                continue
            pos = self._pos_to_coord(cell[0], cell[1])
            basic.left_mouse_click(self.handle, [pos])
            time.sleep(0.1)


if __name__ == "__main__":
    handle = basic.get_handle()
    floor = Floor(handle)
    start = floor.find_door_pos(handle)
    targets = floor.find_monsters_pos(handle)
    obstacles = floor.find_obstacles_pos(handle)
    print(obstacles)

    shortest_path = floor.find_shortest_path_through_all_targets(
        start, targets, obstacles
    )
    if shortest_path:
        print("最短路径:", shortest_path)
    else:
        print("未找到路径")

    floor.click_via_path(shortest_path)
