/* global use, db */
// MongoDB Playground
// To disable this template go to Settings | MongoDB | Use Default Template For Playground.
// Make sure you are connected to enable completions and to be able to run a playground.
// Use Ctrl+Space inside a snippet or a string literal to trigger completions.
// The result of the last command run in a playground is shown on the results panel.
// By default the first 20 documents will be returned with a cursor.
// Use 'console.log()' to print to the debug output.
// For more documentation on playgrounds please refer to
// https://www.mongodb.com/docs/mongodb-vscode/playgrounds/

// Select the database to use.
use('orientation_db');

db.getCollection('files').deleteMany({});

// Insert a few documents into the sales collection.
// db.getCollection('files').updateMany(
//     { 'filename': 'Before Orientation.docx' },
//     { $set: { 'file_type': 'docx', 'uploaded_at': new Date() } },
//     { upsert: true }
//   );
  
//   db.getCollection('files').updateMany(
//     { 'filename': 'During Orientation Week.docx' },
//     { $set: { 'file_type': 'docx', 'uploaded_at': new Date() } },
//     { upsert: true }
//   );
  
//   db.getCollection('files').updateMany(
//     { 'filename': 'Full Time Orientation Schedule.docx' },
//     { $set: { 'file_type': 'docx', 'uploaded_at': new Date() } },
//     { upsert: true }
//   );
  
//   db.getCollection('files').updateMany(
//     { 'filename': 'Part Time Orientation Schedule.docx' },
//     { $set: { 'file_type': 'docx', 'uploaded_at': new Date() } },
//     { upsert: true }
//   );

//   db.getCollection('files').updateMany(
//     { 'filename': 'TR1S-Full-Time-Orientation-Schedule.pdf' },
//     { $set: { 'file_type': 'pdf', 'uploaded_at': new Date() } },
//     { upsert: true }
//   );  
    

  db.getCollection('files').updateMany(
    { 'filename': 'Orientation Info.docx' },
    { $set: { 'file_type': 'docx', 'uploaded_at': new Date() } },
    { upsert: true }
  );

  db.getCollection('files').updateMany(
  {'filename': 'index_faiss'},
   {"$set": {
    "file_type": "faiss",'uploaded_at': new Date()
    }},
  { upsert: true}
  );

  db.getCollection('files').updateMany(
    {'filename': 'index_pkl'},
     {"$set": {
      "file_type": "pkl",'uploaded_at': new Date()
      }},
    { upsert: true}
    );

// Query the files stored in the database
const fileCount = db.getCollection('files').countDocuments();
console.log(`Total uploaded files: ${fileCount}`);

// Show all files
db.getCollection('files').find().toArray();
