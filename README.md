# Lake
 A Simulation of an AI Controlled Traffic Flow Management System using Reinforcement Learning

USER’S MANUAL
1.0  GENERAL INFORMATION
    1.1  System Overview
        LAKE is a Traffic Flow Management System integrated with Artificial Intelligence with the purpose of reducing traffic congestion and vehicular queuing along intersections. It monitors current traffic situations to identify the appropriate action to take. It can adjust traffic phases based on the present traffic situation along an intersection.
    1.2  Authorized Use Permission
        The Simulation of an AI Controlled Traffic Flow Management System is available to the public. You do not need an account to navigate through the system.

2.0  QUICK GUIDE
    2.1  Software Requirements
        Ø  SUMO v1.10 – (Simulation of Urban MObility)
        Ø  Windows operating system
    2.2  Hardware Requirements
        Ø  Processor at least Intel Core i5 equivalent or higher
        Ø  RAM at least 4gb
    2.3  Installation
    The following steps are made to access LAKE – A Simulation of an AI Controlled Traffic Flow Management System:
        1. Download .rar file
        2. Extract .rar file
        3. Open Lake.exe to start the system

3.0  SYSTEM FEATURES
    3.1  Home Page
        Opening the system would prompt you to the LAKE Home Page GUI showing the system’s overview. By clicking the SIMULATE button would bring you to the next page
    3.2  Load Model Page
        In this page, you can choose the simulation environment that would be shown in the SUMO GUI. You can choose either of the four scenarios namely 1 Traffic Light (1TL), 2 Traffic Lights (2TL), 7 Traffic Lights (7TL) and Roxas Boulevard which is based on the data provided by the MMDA.
        Clicking the START SIMULATE would close the application and open the SUMO GUI. While the GO BACK button would prompt you back to the Home Page.
    3.3  SUMO GUI
        The newly opened window is the SUMO API’s GUI. This window would visually simulate the selected model.
    3.4  Traffic Light System
        The system is integrated with Artificial Intelligence that was trained by the developers to analyze and handle the vehicular queuing along intersections.
        3.4.1  Monitoring
            The system’s AI could monitor present traffic situations by getting the position, velocity, and the current traffic phase within an intersection. A maximum of 16 cars per lane is the limit of the AI’s visibility.
        3.4.2  Dynamic Phase Change
            The system’s AI could dynamically change the traffic phase based on the present situation at a certain intersection. It could either change to a different phase or keep the current phase. The traffic phase duration is at 10 seconds green phase and 5 seconds’ yellow phase.
        3.5  Traffic Data Report
            After each simulation, the system generates a traffic data report represented in a graph. It records the cumulative waiting times and the average queue length of each intersection. This graph can be seen by navigating through the system file folder and going to the “models” folder.
