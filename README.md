# Lake
 A Simulation of an AI Controlled Traffic Flow Management System using Reinforcement Learning

<<<<<<< HEAD
USER’S MANUAL <br />
1.0  GENERAL INFORMATION <br />
    1.1  System Overview <br />
        <p>LAKE is a Traffic Flow Management System integrated with Artificial Intelligence with the purpose of reducing traffic congestion and vehicular queuing along intersections. It monitors current traffic situations to identify the appropriate action to take. It can adjust traffic phases based on the present traffic situation along an intersection. </p>
    1.2  Authorized Use Permission <br />
        The Simulation of an AI Controlled Traffic Flow Management System is available to the public. You do not need an account to navigate through the system.

2.0  QUICK GUIDE <br />
    2.1  Software Requirements <br />
        Ø  SUMO v1.10 – (Simulation of Urban MObility) <br />
        Ø  Windows operating system <br />
    2.2  Hardware Requirements <br />
        Ø  Processor at least Intel Core i5 equivalent or higher <br />
        Ø  RAM at least 4gb <br />
    2.3  Installation <br />
    The following steps are made to access LAKE – A Simulation of an AI Controlled Traffic Flow Management System: <br />
        1. Download .rar file <br />
        2. Extract .rar file <br />
        3. Open Lake.exe to start the system <br />

3.0  SYSTEM FEATURES <br />
    3.1  Home Page <br />
        <p>Opening the system would prompt you to the LAKE Home Page GUI showing the system’s overview. By clicking the SIMULATE button would bring you to the next page </p><br />
    3.2  Load Model Page <br />
        <p>In this page, you can choose the simulation environment that would be shown in the SUMO GUI. You can choose either of the four scenarios namely 1 Traffic Light (1TL), 2 Traffic Lights (2TL), 7 Traffic Lights (7TL) and Roxas Boulevard which is based on the data provided by the MMDA. <br />
        Clicking the START SIMULATE would close the application and open the SUMO GUI. While the GO BACK button would prompt you back to the Home Page. </p> <br />
    3.3  SUMO GUI <br />
        <p>The newly opened window is the SUMO API’s GUI. This window would visually simulate the selected model. </p> <br />
    3.4  Traffic Light System <br />
        <p>The system is integrated with Artificial Intelligence that was trained by the developers to analyze and handle the vehicular queuing along intersections. </p> <br />
        3.4.1  Monitoring <br />
            <p>The system’s AI could monitor present traffic situations by getting the position, velocity, and the current traffic phase within an intersection. A maximum of 16 cars per lane is the limit of the AI’s visibility. </p> <br />
        3.4.2  Dynamic Phase Change <br />
            <p>The system’s AI could dynamically change the traffic phase based on the present situation at a certain intersection. It could either change to a different phase or keep the current phase. The traffic phase duration is at 10 seconds green phase and 5 seconds’ yellow phase. </p> <br />
        3.5  Traffic Data Report <br />
            <p>After each simulation, the system generates a traffic data report represented in a graph. It records the cumulative waiting times and the average queue length of each intersection. This graph can be seen by navigating through the system file folder and going to the “models” folder.</p> 
=======
Software Requirements:
- SUMO v1.10
- CUDA v11.2
- cuDNN v8.1
- Python libraries @ requirements.txt

How to run:
- TRAINING
    - Edit train_settings.ini for configuration
    - Run train.py
    - After training, the model will be saved at models folder

- TESTING
    - Edit test_settings.ini and match the models parameters
    - Run test.py
>>>>>>> parent of 172a06a (Update README.md)
