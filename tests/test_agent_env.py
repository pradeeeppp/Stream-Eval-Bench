"""Unit tests for Stream-Eval-Bench Agent Environment."""

import unittest
import json
from stream_eval.core.models import VideoPacket, Observation
from stream_eval.core.schedules import (
    ChronologicalSchedule,
    DelayedSchedule,
    TogetherSchedule,
    DropSchedule,
)
from stream_eval.core.environment import StreamingEnvironment, parse_json_response
from stream_eval.core.agents import MockAgent
from stream_eval.core.evaluator import StreamEvaluator
from stream_eval.usecases.registry import get_usecase, list_usecases


class TestStreamingEnvironment(unittest.TestCase):

    def setUp(self):
        self.p1 = VideoPacket(packet_id="p1", capture_start=10.0, capture_end=20.0)
        self.p2 = VideoPacket(packet_id="p2", capture_start=25.0, capture_end=35.0)
        self.p3 = VideoPacket(packet_id="p3", capture_start=40.0, capture_end=50.0)
        self.all_packets = [self.p1, self.p2, self.p3]

    def test_schedules(self):
        # Chronological
        chrono = ChronologicalSchedule()
        steps = chrono.organize_steps([self.p2, self.p1, self.p3])
        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[0][0].packet_id, "p1")
        self.assertEqual(steps[1][0].packet_id, "p2")
        self.assertEqual(steps[2][0].packet_id, "p3")

        # Together
        together = TogetherSchedule()
        t_steps = together.organize_steps(self.all_packets)
        self.assertEqual(len(t_steps), 1)
        self.assertEqual(len(t_steps[0]), 3)

        # Delayed (delay earliest packet)
        delayed = DelayedSchedule(delay_by_steps=1)
        d_steps = delayed.organize_steps(self.all_packets)
        self.assertEqual(len(d_steps), 3)
        self.assertEqual(d_steps[0][0].packet_id, "p2")
        self.assertEqual(d_steps[1][0].packet_id, "p1")
        self.assertEqual(d_steps[2][0].packet_id, "p3")

        # Drop
        drop = DropSchedule(drop_packet_ids=["p2"])
        dr_steps = drop.organize_steps(self.all_packets)
        self.assertEqual(len(dr_steps), 2)
        self.assertEqual([s[0].packet_id for s in dr_steps], ["p1", "p3"])

    def test_json_parsing(self):
        # Direct json
        self.assertEqual(parse_json_response('{"a": 1}'), {"a": 1})
        # Embedded in markdown or text
        self.assertEqual(
            parse_json_response('Here is my answer: {"earlier": "no", "latest": "yes"} thanks!'),
            {"earlier": "no", "latest": "yes"},
        )
        # Invalid
        self.assertIsNone(parse_json_response("No json here"))

    def test_table_assembly_usecase(self):
        uc = get_usecase("table_assembly_tray")
        self.assertEqual(uc.usecase_id, "table_assembly_tray")
        self.assertEqual(len(uc.packets), 2)

        # 1. Oracle run on Chronological
        oracle_agent = MockAgent(
            preset_answers={
                "chronological_0": {"earlier": "no", "latest": "no"},
                "chronological_1": {"earlier": "no", "latest": "yes"},
                "delayed_0": {"earlier": "unknown", "latest": "yes"},
                "delayed_1": {"earlier": "no", "latest": "yes"},
                "together_0": {"earlier": "no", "latest": "yes"},
            }
        )

        env = StreamingEnvironment(usecase=uc, schedule="chronological")
        res_chrono = env.run_episode(oracle_agent)
        self.assertEqual(res_chrono.metrics["final_accuracy"], 1.0)
        self.assertEqual(res_chrono.metrics["trajectory_fidelity"], 1.0)

        # 2. Oracle run on Delayed
        env_delayed = StreamingEnvironment(usecase=uc, schedule="delayed")
        res_delayed = env_delayed.run_episode(oracle_agent)
        self.assertEqual(res_delayed.metrics["final_accuracy"], 1.0)
        self.assertEqual(res_delayed.metrics["historical_update_success"], True)
        self.assertEqual(res_delayed.metrics["recency_preserved"], True)

    def test_intermediate_error_detection(self):
        uc = get_usecase("table_assembly_tray")
        # Agent mimics the intermediate error where step 0 says yes instead of no
        agent = MockAgent(mode="intermediate_error")
        env = StreamingEnvironment(usecase=uc, schedule="chronological")
        res = env.run_episode(agent)

        # Final accuracy is 100%, but trajectory fidelity is 0.75 (step 0 had 1/2 correct)
        self.assertEqual(res.metrics["final_accuracy"], 1.0)
        self.assertEqual(res.metrics["perfect_trajectory"], False)
        self.assertLess(res.metrics["trajectory_fidelity"], 1.0)

    def test_camera_detachment_usecase(self):
        uc = get_usecase("camera_detachment")
        self.assertEqual(uc.usecase_id, "camera_detachment")
        self.assertEqual(len(uc.packets), 6)

        # Together schedule
        env = StreamingEnvironment(usecase=uc, schedule="together")
        obs = env.reset()
        self.assertEqual(len(obs.packets), 6)
        self.assertEqual(obs.latest_capture_boundary, 24.0)

        # Step with expected final
        _, step_res, done, _ = env.step(uc.expected_final)
        self.assertTrue(done)
        self.assertEqual(step_res.step_metrics["accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()
