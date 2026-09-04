from threading import Event

class TrainingState:

    def __init__(self):

        self.running = False
        self.paused = False

        self.pause_event = Event()

        self.pause_event.set()

training_state = TrainingState()