from flask import Flask, render_template, request, redirect, url_for, jsonify
from dataclasses import dataclass, asdict
from typing import List, Dict

GAME_STATES = [
    "welcome",
    "question_pending",
    "answering_question",
    "voting_answer",
    "showing_answers",
    "showing_score"
]

SCORE_FOR_VOTING_CORRECTLY = 50
SCORE_FOR_TRICKING_OTHERS = 20

@dataclass
class Player:
    username: str
    question_answer_pairs: Dict[str, str]
    question_people_that_voted_for_my_answer_pairs: Dict[str, List[str]]
    question_person_i_voted_for_pairs: Dict[str, str]
    question_score_earned_pairs: Dict[str, int]
    score: int

    def add_new_question(self, question: str):
        self.question_answer_pairs[question] = None
        self.question_people_that_voted_for_my_answer_pairs[question] = []
        self.question_person_i_voted_for_pairs[question] = None
        self.question_score_earned_pairs[question] = None

    def compute_score_for_question(self, question: str, correct_person: str):
        score_from_trickery = len(self.question_people_that_voted_for_my_answer_pairs[question]) * SCORE_FOR_TRICKING_OTHERS
        score_from_my_vote = SCORE_FOR_VOTING_CORRECTLY if self.question_person_i_voted_for_pairs[question] == correct_person else 0
        total_score_for_this_question = score_from_trickery + score_from_my_vote
        self.question_score_earned_pairs[question] = total_score_for_this_question
        overall_score = 0
        for question in self.question_score_earned_pairs:
            overall_score += self.question_score_earned_pairs[question]
        self.score = overall_score
        return total_score_for_this_question


@dataclass
class GameData:
    players: Dict[str, Player]
    current_state: str
    questions: List[str]
    current_question_idx: int
    correct_person_username: str


    

# Initialize
app = Flask(__name__)
game_data = GameData(
    players={},
    current_state=GAME_STATES[0],
    questions=[],
    current_question_idx=-1,
    correct_person_username="KingIvan"
    )

def reinitialize_the_awesome():
    global game_data
    game_data = GameData(
    players={},
    current_state=GAME_STATES[0],
    questions=[],
    current_question_idx=-1,
    correct_person_username="KingIvan"
    )

@app.route("/")
def index():
    return redirect(url_for('player'))

@app.route("/player", methods=["GET"])
def player():
    return render_template("player.html")

@app.route("/projector", methods=["GET"])
def projector():
    return render_template("projector.html")

@app.route("/ivan", methods=["GET"])
def ivan():
    return render_template("ivan.html")

@app.route("/admin", methods=["GET"])
def admin():
    return render_template("admin.html")

@app.route("/get_game_data", methods=["GET"])
def get_game_data():
    return jsonify(asdict(game_data))

@app.route("/advance_game_state", methods=["GET"])
def advance_game_state():
    global game_data
    current_state = game_data.current_state
    current_state_idx = GAME_STATES.index(current_state)
    next_state_idx = current_state_idx + 1
    if next_state_idx == len(GAME_STATES):
        next_state_idx = 1 # question_pending
    next_state = GAME_STATES[next_state_idx]
    game_data.current_state = next_state
    return jsonify({"advance_game_state_success": True})

@app.route("/start_over", methods=["GET"])
def start_over():
    reinitialize_the_awesome()
    return jsonify({"start_over_success": True})

@app.route("/add_ivan", methods=["POST"])
def add_ivan():
    global game_data
    posted_payload = request.get_json()
    ivan_username = posted_payload.get("new_player_username")
    new_player = Player(
        username=ivan_username,
        question_answer_pairs={},
        question_people_that_voted_for_my_answer_pairs={},
        question_person_i_voted_for_pairs={},
        question_score_earned_pairs={},
        score=0,
        )
    game_data.players[ivan_username] = new_player
    game_data.correct_person_username = ivan_username
    print(ivan_username)
    return jsonify({"add_ivan_success": True})

@app.route("/add_new_player", methods=["POST"])
def add_new_player():
    global game_data
    posted_payload = request.get_json()
    new_player_username = posted_payload.get("new_player_username")
    new_player = Player(
        username=new_player_username,
        question_answer_pairs={},
        question_people_that_voted_for_my_answer_pairs={},
        question_person_i_voted_for_pairs={},
        question_score_earned_pairs={},
        score=0,
        )
    game_data.players[new_player_username] = new_player

    print(new_player_username)
    return jsonify({"add_new_player_success": True})

@app.route("/add_new_question", methods=["POST"])
def add_new_question():
    global game_data
    posted_payload = request.get_json()
    new_question = posted_payload.get("new_question")
    game_data.questions.append(new_question)
    game_data.current_question_idx += 1

    for player_username in game_data.players:
        game_data.players[player_username].add_new_question(new_question)

    print(new_question)
    return jsonify({"add_new_question_success": True})

@app.route("/add_new_answer_to_current_question", methods=["POST"])
def add_new_answer_to_current_question():
    global game_data
    posted_payload = request.get_json()
    new_answer = posted_payload.get("new_answer")
    player_username = posted_payload.get("player_username")
    current_question = game_data.questions[game_data.current_question_idx]
    game_data.players[player_username].question_answer_pairs[current_question] = new_answer

    print(new_answer)
    return jsonify({"add_new_answer_to_current_question_success": True})

@app.route("/vote_for_user", methods=["POST"])
def vote_for_user():
    global game_data
    posted_payload = request.get_json()
    player_username = posted_payload.get("player_username")
    voted_for_username = posted_payload.get("voted_for_username")
    current_question = game_data.questions[game_data.current_question_idx]

    game_data.players[player_username].question_person_i_voted_for_pairs[current_question] = voted_for_username
    game_data.players[voted_for_username].question_people_that_voted_for_my_answer_pairs[current_question].append(player_username)

    print(f"{player_username} voted for {voted_for_username}")
    return jsonify({"vote_for_user_success": True})

@app.route("/compute_scores_for_the_round")
def compute_scores_for_the_round(methods=["GET"]):
    global game_data
    current_question = game_data.questions[game_data.current_question_idx]
    for player_username in game_data.players:
        game_data.players[player_username].compute_score_for_question(current_question, correct_person=game_data.correct_person_username)
    return jsonify(asdict(game_data))



if __name__ == '__main__':
    app.run(debug=False)
