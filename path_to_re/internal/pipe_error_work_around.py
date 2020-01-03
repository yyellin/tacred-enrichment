def revert_to_default_behaviour_on_sigpipe():
    # https://stackoverflow.com/questions/14207708/ioerror-errno-32-broken-pipe-python

    try:
        from signal import signal, SIGPIPE, SIG_DFL

        signal(SIGPIPE, SIG_DFL)
    except:
        pass