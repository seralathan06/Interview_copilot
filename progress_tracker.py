import json
import os

class ProgressTracker:
    def __init__(self, data_dir: str = "data"):
        """
        Initializes the ProgressTracker.
        Args:
            data_dir: The directory where progress files are stored.
        """
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True) # Ensure the data directory exists

    def _get_progress_file_path(self, user_id: str) -> str:
        """Constructs the path to the user's progress file."""
        return os.path.join(self.data_dir, f"progress_{user_id}.json")

    def load_progress(self, user_id: str) -> dict:
        """
        Loads the progress for a specific user from their progress file.
        If the file doesn't exist, returns an empty dictionary.
        """
        progress_file = self._get_progress_file_path(user_id)
        if os.path.exists(progress_file):
            try:
                with open(progress_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: progress_file for user {user_id} is corrupted. Starting fresh.")
                return {"score": {"correct": 0, "total": 0}, "answers": {}}
        # Initialize structure for a new user
        return {"score": {"correct": 0, "total": 0}, "answers": {}}

    def save_progress(self, user_id: str, progress_data: dict):
        """
        Saves the progress data for a specific user to their progress file.
        """
        progress_file = self._get_progress_file_path(user_id)
        with open(progress_file, "w", encoding="utf-8") as f:
            json.dump(progress_data, f, indent=2)

    def record_answer(self, user_id: str, question_id: int, is_correct: bool):
        """
        Records an answer for a specific question for a given user.
        Updates the overall score and saves the individual answer status.
        """
        progress = self.load_progress(user_id)

        # Update individual question status
        str_q_id = str(question_id)
        
        # Check if this question was already answered
        already_answered_correctly = progress["answers"].get(str_q_id, {}).get("correct")
        
        # Update score only if it's the first time or if the previous answer was wrong and this is correct
        if str_q_id not in progress["answers"]:
            progress["score"]["total"] += 1
            if is_correct:
                progress["score"]["correct"] += 1
        elif not already_answered_correctly and is_correct:
            # If they previously got it wrong, but now got it correct (on a retry, for example)
            progress["score"]["correct"] += 1
        
        # Always update the last answer status for the question
        progress["answers"][str_q_id] = {"correct": is_correct}
        
        self.save_progress(user_id, progress)

    def get_score(self, user_id: str) -> dict:
        """
        Retrieves the current score (correct answers, total questions, and accuracy)
        for a specific user.
        """
        progress = self.load_progress(user_id)
        correct = progress["score"]["correct"]
        total = progress["score"]["total"]
        accuracy = (correct / total) * 100 if total > 0 else 0.0
        
        return {
            "correct": correct,
            "total": total,
            "accuracy": accuracy
        }

# Example Usage (for testing the module directly)
# if __name__ == "__main__":
#     tracker = ProgressTracker()
#     test_user_id = "test_user_123"

#     print(f"Initial score for {test_user_id}: {tracker.get_score(test_user_id)}")

#     print("\nRecording answer for Q1 (correct)...")
#     tracker.record_answer(test_user_id, 1, True)
#     print(f"Score after Q1: {tracker.get_score(test_user_id)}")

#     print("\nRecording answer for Q2 (incorrect)...")
#     tracker.record_answer(test_user_id, 2, False)
#     print(f"Score after Q2: {tracker.get_score(test_user_id)}")

#     print("\nRecording answer for Q3 (correct)...")
#     tracker.record_answer(test_user_id, 3, True)
#     print(f"Score after Q3: {tracker.get_score(test_user_id)}")
    
#     print("\nRe-recording answer for Q2 (now correct)...")
#     tracker.record_answer(test_user_id, 2, True) # User retries and gets it right
#     print(f"Score after Q2 retry: {tracker.get_score(test_user_id)}")

#     print("\nRecording answer for Q1 again (still correct - no change in score, just updates answer status)...")
#     tracker.record_answer(test_user_id, 1, True)
#     print(f"Score after Q1 again: {tracker.get_score(test_user_id)}")

#     # Test another user
#     another_user_id = "another_user"
#     print(f"\nInitial score for {another_user_id}: {tracker.get_score(another_user_id)}")
#     tracker.record_answer(another_user_id, 10, True)
#     print(f"Score for {another_user_id}: {tracker.get_score(another_user_id)}")

    # Clean up test files if desired
    # import glob
    # for f in glob.glob("data/progress_*.json"):
    #     os.remove(f)