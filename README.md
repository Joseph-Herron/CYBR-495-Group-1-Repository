            Project Description:
Consist on the development of a secure database system for storing and managing sensitive satellite imagery and associated metadata. Satellite images can contain sensitive geographic information, including coordinates, timestamps, and other information that could potentially be misused if accessed by unauthorized indivuals .

This system will implement multiple layers of security to protect this information. These security measures will include encryption, secure encryption key management, authentication, role - based access control(RBAC), and potentially location - based access control (LBAC).

Sponsors- Dr. Wang & Dr. Pharris will represent us as our sponsors giving us guidance, feedback, and oversight throught the development process

            Project Objectives:
1.Develop a secure database for storing satellite imagery and metadata.
2.Encrypt sensitive satellite images and metadata before they are stored.
3.Protect encryption keys using a dedicated secrets- management system.
4.Implement authentication for users accessing the system. 
5.Implement role - based access control for different categories of users. 
6.Restricts users from accessing data outside their assigned permissions.
7.Detect any unauthorized midufucation without altering or tampering stored data.
8.Testing the system against simulated database breaches and unauthorized access attempts.
9.Explore the possibilty of using geographic restrictions to control access to satellite data.
 
            Scope of project:
    Encryption - system will provide functionally for
Encrypting satellite images & ,metadata. 
Decrypting data for authorized users.
Preventing unauthorized users from accessing plaintext data.
Seperating encryption key management from the primary database(Encrypted keys wil not be stored alongside the encrypted satellite data).

    Access control 
This system will implement role-based access control using three primary roles.
    1.Administrator
Administrator will have the highest level of access.
Their permissions will consists of:
    - Create and manage users
    - Assign roles
    - Manage access permissions
    - Upload satellite data
    - View satallite data
    - Delete or modify authorized data
    - Manage system configuration

    2.Analyst
Analyst will have access to data required for analysis but will have fewer priviliges than a administrator.
Their permissions will consist of:
    - View authorized satellite imagery 
    - Accessed authorized metadata.
    - Perform analysis on satellite imagery
    - Search for satellite data
    - Download or process authorized data

    Analyst wil not have administrative priviliges or access to encryption keys. 

    3.Viewer
Viewers will have the most restricted access.
Their permissions will consist of: 
    - View authorized satellite imagery
    - View non-sensitive metadata
    
    Viewers will not be able to modify data, manage users, or access the encryption keys.



            Technical Approach:
 1.Python + FastAPI  - Backend
Python will be our pimary programming language.
FastAPI will be used to develop the backend API responsible for communicating between users, authentication services, the database, and security components. 
The backend will be responsible for 
    - Processing API request
    - Authenticating users. 
    - Checking user permissions 
    - Encrypting and decrypting data 
    - Enforcing access - control policies
    - Logging security - related events 
    (Maybe communicating with Postgre SQL & HashiCorp Vault)
2.Database -PostgreSQL
PostgreSQL will be used as the primary database.
Database will store information such as: 
    - Encrypted satellite images & Metadata
    - Image Identifiers?
    - User - related information required by the application
    - Geographic information 
    - Timestamps ?
    - Access control information


3.Encryption and key management -HashiCorp Vault
HashiCorp Vault will be used for managing and protecting encryption keys and other secrets.
We will use the Vault as a way to seperate encryption key- management from the PostgreSQL databse. 
        Idea of the process
1.User uploads satellite data. 
2.The FastAPI backend recieves the data.
3.The backend request the appropiate encryption key from Vault.
4.Satellite images and sensitive metadata  are encrpyted.
5.Encrypted data is stored in PostgreSQL.
6.Key remains protected by the Vault.
7.When a authorized user request the data, the backend retrieves the required key from the Vault.
8.The backend decrypts the data
9.The user recives the authorized data

To sum that up Users should not have direct access to th encryption keys

4.Keycloak 
Keycloak will be used for authentication and role management.

Keycloak services provide: 
    - User authentication
    - User accounts
    - Role assignments
    - Access tokens
    - Authentication management 
This application will enforc permissions on the backend.

5.Geospatial Processing - GeoPandas
GeoPandas may be used to process geographic information associated with satellite imagery. 
Ways it can be used: 
    - Processing geographic coordinates
    - Working with geographic boundaries
    - Determining wheter coordinates fall within authorized regions
    - Supporting location - based access control
    - Filtering satellite images by geographic area



Testing: 

1.Encryption/Decryption — Verify encrypted images and metadata can be accurately recovered by authorized users.We will test this throughout the 10 weeks rather than just the end of the project

Testing this shall verify that: 
    - Encrypted files cannot be interpereted as plaintext​
    - Authorized users can recover original data
    - Decryption produces the correct original file
    - Incorrect or unauthorized keys cannot decrypt data

2.Database Breach Simulation — Confirm stolen database contents do not reveal sensitive plaintext data. ​
Testing this will verify that: 
    - Senesitive information isn't stored as plaintext
    - Encrption kets aren't stored in the database
    - Stolen database contents cannt easily be converted back into the original satellite data


3.RBAC Testing — Verify Admin, Analyst, and Viewer permissions are correctly enforced. We will do this by testing them all seperatly and make sure Admins can access administrative functions, Viewers can't modify data, and make sure Analyst aren't able to access information outside their permissions. 


4.Tamper Detection — Encrypted data will be intentionally modified to determine if the system notice these unauthorized changes.
When it's successful it will prove that: 
    - Modified encrypted data is detected
    - Invalid data is not silently accepted
    - System doesn't return corrupted plaintext as valid data


5.Unauthorized Access — Many attempts will be made to bypass Authentication, Role restricions, Data permissions, Geographic restrictions, API authorization checks 

6.Key management testing 
Testing will verify that: 
    - Encryption keys aren't stored in PostgreSQL
    - Users can't directly retrieve encryption keys 
    - Application retireves keys only when it has to
    - Unauthorized request cannot retrieve protected keys


## Authentication and Role-Based Access Control (RBAC)

### Overview
The project uses Keycloak for user authentication and FastAPI for role-based authorization. Users must provide a valid Keycloak access token to access protected API endpoints.

### Configured Roles
- **Admin:** Can list satellite images and retrieve images.
- **Analyst:** Can list satellite images and retrieve images.
- **Viewer:** Can retrieve individual satellite images but cannot access the image listing endpoint.

### Protected API Endpoints
- `GET /images` — Accessible to Admin and Analyst roles.
- `GET /images/{image_id}/view` — Accessible to Admin, Analyst, and Viewer roles.

### Security Testing Results

| Test | Expected Result | Actual Result |
|---|---|---|
| Admin lists images | HTTP 200 | Passed |
| Analyst lists images | HTTP 200 | Passed |
| Viewer lists images | HTTP 403 | Passed |
| Viewer retrieves image 1 | HTTP 200 | Passed |
| Request without an access token | HTTP 401 | Passed |



### Results

Testing confirmed that Keycloak-issued access tokens are accepted by the API and that endpoint access is restricted according to the user's assigned role. Unauthorized requests are rejected, while permitted requests succeed.

*Note: These results reflect the tests completed so far. Additional testing is needed to verify all role and endpoint combinations.*


*Note: These results reflect the tests completed so far. Additional testing is needed to verify all role and endpoint combinations.*