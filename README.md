# Takt Feedback Report

## Run the web app locally

1. Install Python 3.10 or newer.
2. Install the project dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Add your Gemini API key to the project's `.env` file:

   ```text
   GEMINI_API_KEY=your_api_key
   TAKT_APP_PASSWORD=choose_a_long_unique_password
   TAKT_SECRET_KEY=generate_a_long_random_secret
   ```

4. Start the app from a terminal:

   ```powershell
   python web_app.py
   ```

   Or, after setup, double-click `start_takt.bat` to launch it and open the page.

5. If you started it from a terminal, open <http://127.0.0.1:5000> in your browser.

The page accepts one feedback comment per line, SQLite database files with a
`TrainingFeedback` table (the feedback column defaults to `Comments`), or Excel
`.xlsx` / `.xlsm` files with a column headed `הערות`. The Excel loader extracts
non-empty cells below that header before sending feedback to Gemini. In the web
form, enter a different header or SQLite column name when your file uses another
column title. The workflow runs four Gemini stages—split, professional
refinement, deduplication, and categorization—then provides a Hebrew Excel
report. Split and professional refinement process batches of 20.

The web page includes editable Hebrew category names and descriptions. Category
changes are saved in that browser's local storage and sent to Gemini with each
submitted job; they are not shared across browsers or saved on the server.

Gemini 503 errors receive a small number of delayed retries. Other API errors,
including quota errors, are reported without automatic retries.

Uploaded databases are written to a temporary directory and removed after
reading. Feedback is sent to Gemini for processing. The app binds to localhost
by default and is not publicly accessible; deploy it with appropriate access
controls before sharing it over the internet. Never commit the `.env` file.

## Deploy on Render

1. Push this project to a private GitHub repository. Do not commit `.env` or
   include API keys in source files.
2. In Render, create a new **Blueprint** and connect the repository. Render will
   read `render.yaml` and configure the Python web service.
3. In the Render service's environment settings, add values for
   `GEMINI_API_KEY` and `TAKT_APP_PASSWORD`. Use a long, unique password for
   app access; the generated `TAKT_SECRET_KEY` and secure-cookie setting are
   already configured by the Blueprint.
4. Deploy the service and open its `onrender.com` URL. Share that URL and the
   app password only with intended users.

The app uses in-memory job storage; a server restart clears active jobs and
completed reports.
Choose a Render plan that meets your usage needs. Anyone with the app password
can run jobs that use your Gemini API quota.
