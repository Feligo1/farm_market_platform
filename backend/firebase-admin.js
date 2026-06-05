const admin = require('firebase-admin');
const serviceAccount = require('./firebase-config/farm-market-platform-firebase-adminsdk-fbsvc-061ddd20f6.json');

// Initialize Firebase Admin
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: "https://farm-market-platform.firebaseio.com", // You may need to add this
});

// Export for use in other files
const db = admin.firestore();
const auth = admin.auth();
const storage = admin.storage();

module.exports = { admin, db, auth, storage };