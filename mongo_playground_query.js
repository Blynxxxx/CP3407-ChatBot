
db.getCollection('vector_store').updateOne(
    { filename: "orientation_index" },
    {
        $set: {
            file_type: "faiss",
            uploaded_at: new Date(),
            
        }
    },
    { upsert: true }
);
