# Summary
The first attempt at making a music player app with the following features:
- Linking songs so that when a playlist is shuffled, those songs always play back-to-back.
- Marking songs as clones of each other, with the ability to configure the percent chance each of the songs play. This may be useful to link covers together with custom priority. For example, you could mark a cover of a song as a clone and give it a 0% chance to play, so that only the original song will play.
- Downstream playlists that will automatically add any songs to its upstream playlists. This is done by treating the downstream playlist as an entity in the upstream playlist, rather than the songs themselves.

This is a console application that uses a json configuration file to track locations of mp3 files provided as input.

# Environment

This is my first time making a python repo, so this may be common knowledge, but I am using `pipenv` to to manage pip dependencies for this project. Therefore:
1. Install pipenv using `pip install pipenv`.
2. Install all packages for this project using `pipenv install`.
3. When adding new pip dependencies, please use `pipenv install <package>`, which will add the package to the project pipfile. See https://packaging.python.org/en/latest/tutorials/managing-dependencies/ for info on pipenv.
4. Initialize the pipenv virtual environment with `pipenv run`.
5. Specify the virtual environment directory via the `python.pythonPath` setting in your vscode settings file in "./.vscode/settings.json". This path will likely be something like "/Users/user/.local/share/virtualenvs/TheGoodPart".

"main.py" is the entrypoint for this application.

# Known issues:
- When playing playlists, transitions between songs are not seamless. Since the application is waiting for the user to enter commands, it requires pressing enter before the next song will play.