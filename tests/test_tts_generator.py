import asyncio
import os
import shutil
import tempfile
import unittest

from services.tts.generator import generate_voiceover


class TestTTSGenerator(unittest.TestCase):
    def test_generate_voiceover_works_inside_running_loop(self):
        temp_dir = os.path.join(os.getcwd(), "assets", "test_tmp")
        os.makedirs(temp_dir, exist_ok=True)
        output_path = os.path.join(temp_dir, "loop_test.mp3")

        async def run_test():
            return generate_voiceover("hello from async test", output_path)

        try:
            result = asyncio.run(run_test())
            self.assertTrue(os.path.exists(result))
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
            if os.path.isdir(temp_dir) and not os.listdir(temp_dir):
                os.rmdir(temp_dir)


if __name__ == "__main__":
    unittest.main()
