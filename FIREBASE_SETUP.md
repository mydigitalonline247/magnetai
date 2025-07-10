# Firebase Authentication Setup for MagnetAI

## Prerequisites
- Firebase project (https://console.firebase.google.com/)
- Service account credentials (JSON file)
- FastAPI backend (Python)

## Step 1: Create a Firebase Project
1. Go to the [Firebase Console](https://console.firebase.google.com/).
2. Click "Add project" and follow the prompts.
3. In the project, go to **Project settings > Service accounts**.
4. Click "Generate new private key" to download the service account JSON file.

## Step 2: Add Service Account Credentials
1. Place the downloaded JSON file in your project directory (e.g., `firebase-credentials.json`).
2. Add the following to your `.env` file:
   ```
   FIREBASE_CREDENTIALS=./firebase-credentials.json
   ```

## Step 3: Install Dependencies
Run:
```bash
pip install firebase-admin
```

## Step 4: Enable Sign-In Providers
1. In the Firebase Console, go to **Authentication > Sign-in method**.
2. Enable the providers you want (Google, Email/Password, etc.).

## Step 5: Backend Integration
- The backend expects a Firebase ID token from the frontend at the `/auth/firebase` endpoint.
- The backend verifies the token using the Firebase Admin SDK and issues its own JWT for session management.

## Step 6: Update Frontend
- Use Firebase Auth SDK to sign in users and obtain a Firebase ID token.
- Send the ID token to the backend `/auth/firebase` endpoint.

## Example Backend Flow
1. Frontend authenticates user with Firebase Auth (any provider).
2. Frontend sends the Firebase ID token to `/auth/firebase`.
3. Backend verifies the ID token and returns an app-specific JWT and user info.

## Security Notes
- Never commit your service account JSON file to version control.
- Use environment variables to manage secrets.
- Revoke and regenerate credentials if they are ever exposed.

## References
- [Firebase Admin SDK (Python)](https://firebase.google.com/docs/admin/setup)
- [Firebase Authentication Docs](https://firebase.google.com/docs/auth) 