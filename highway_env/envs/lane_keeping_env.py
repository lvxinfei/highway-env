from __future__ import division, print_function, absolute_import
import numpy as np
from gym import spaces
from gym.envs.registration import register

from highway_env.envs.common.abstract import AbstractEnv
from highway_env.road.lane import LineType, SineLane
from highway_env.road.road import Road, RoadNetwork
from highway_env.vehicle.dynamics import BicycleVehicle


class LaneKeepingEnv(AbstractEnv):
    """
        A lane keeping control task.
    """
    @classmethod
    def default_config(cls):
        config = super().default_config()
        config.update({
            "observation": {
                "type": "Kinematics"
            },
            "policy_frequency": 10,
            "steering_range": np.pi / 3,
            "screen_width": 600,
            "screen_height": 200,
            "centering_position": [0.4, 0.5]
        })
        return config

    def define_spaces(self):
        super().define_spaces()
        self.action_space = spaces.Box(-1., 1., shape=(1,), dtype=np.float32)

    def step(self, action):
        self.vehicle.act({
            "acceleration": 0,
            "steering": action * self.config["steering_range"]
        })
        self._simulate()

        obs = self.observation.observe()
        info = {}
        reward = self._reward(action)
        terminal = self._is_terminal()
        return obs, reward, terminal, info

    def _reward(self, action):
        _, lat = self.vehicle.lane.local_coordinates(self.vehicle.position)
        return 1 - (lat/self.vehicle.lane.width)**2

    def _is_terminal(self):
        return False  # not self.vehicle.lane.on_lane(self.vehicle.position)

    def reset(self):
        self._make_road()
        self._make_vehicles()
        return super().reset()

    def _make_road(self):
        net = RoadNetwork()

        lane = SineLane([0, 0], [500, 0], amplitude=5, pulsation=2*np.pi / 50, phase=0,
                        width=10, line_types=[LineType.STRIPED, LineType.STRIPED])
        net.add_lane("a", "b", lane)
        road = Road(network=net, np_random=self.np_random, record_history=self.config["show_trajectories"])
        self.road = road

    def _make_vehicles(self):
        road = self.road
        ego_vehicle = BicycleVehicle(road, road.network.get_lane(("a", "b", 0)).position(30, 0),
                                     velocity=5)
        road.vehicles.append(ego_vehicle)
        self.vehicle = ego_vehicle


register(
    id='lane-keeping-v0',
    entry_point='highway_env.envs:LaneKeepingEnv',
)
