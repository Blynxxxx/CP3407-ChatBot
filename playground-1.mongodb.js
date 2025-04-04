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

  db.getCollection('files').updateMany(
    { 'filename': 'Orientation Info.docx' },
    { $set: { 'file_type': 'docx', 'uploaded_at': new Date() } },
    { upsert: true }
  );

  db.getCollection('files').updateMany(
    { 'filename': 'Orientation Info zh.docx' },
    { $set: { 'file_type': 'docx', 'uploaded_at': new Date() } },
    { upsert: true }
  );

// Query the files stored in the database
const fileCount = db.getCollection('files').countDocuments();
console.log(`Total uploaded files: ${fileCount}`);

// Show all files
db.getCollection('files').find().toArray();

db.fs.files.find({}, { filename: 1, length: 1, uploadDate: 1 }).forEach(file => {
  print(`${file.filename} | size: ${file.length} | uploaded: ${file.uploadDate}`)
})

db.fs.files.find().toArray();