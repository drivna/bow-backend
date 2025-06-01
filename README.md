# bow-backend

# Models

# 1. User `This will store users`
    id 
    name
    email
    password

# 2. Files `This will store all the files we get from user`
    id
    user_id
    filename
    file_content
    created_at
    updated_at
    meta_data

# 3. Content `This will store all the contents we generate for user`
    id
    user_id
    content_type // Summary/Quiz/Document
    content_heading
    content_data -> JSON
    created_at

# 4. Content_user_data `This will store all the responses/feedback we get from user, i.e: answers on quiz`
    id
    content_id
    user_id
    user_inputs
    created_at
    updated_at


# 5. Content_file_relationship `This will store mapping b/w file and content`
    id
    content_id
    file_id
    user_id
    status


# 6. Attachments `This will store every file in attachment`
    id
    user_id
    content_file_id -> `This will be not-null if the document is recived from user`
    content_user_data_file_id  -> `This will be not-null if the document generated is on request from user`
    cloud_file_id
    name
    status
    created_at
    updated_at

# 7. Cloud_files `This will store url/path of file, i.e: cdn/s3`
    id
    url
    status
    created_at
    updated_at

