# Example App

This example app demonstrates how to publish data from a device to be received and stored later in a data pod.

You can use this app as a template to build your own IoT app.
The app is written in Python, but you can also use any other programming language.

# How To Develop

## Foundations with Docker

Apps are created as Docker images. Each app must have a Dockerfile called "Dockerfile" in the top folder. The Dockerfile describes the system setup your application code will run in.
Basically you use the Dockerfile to create a custom linux configuration starting from a standard base image like ubuntu or alpine linux.
Alternatively or additionally you can add Dockerfiles for specific target system architectures "Dockerfile.armv7" or "Dockerfile.arm64" if you want to make your app run on armv7 (Raspberry pi) or arm64 (Jetson) systems.
The "Dockerfile" will be used if there is no specific dockerfile present for that device's system architecture.
Refer to the [official documentation](https://docs.docker.com/engine/reference/builder/) for more information on dockerfiles.

### Docker Compose

Often Apps use different service components like a database and a webserver and it is good practice to seperate these services into different docker containers. To enable you to build these more complex app architectures you can use a docker compose setup with multiple docker containers. Just put a docker-compose.yml in the root folder instead of just a Dockerfile and you are all set. 
This approach gives you more control over volumes and other runtime details for your docker containers. When users start or stop your app on their devices, then the whole docker-compose setup will be started or stopped.

## Editing Code
You can either edit the source code of your app online in the IronFlock integrated code editor or you can use your local development environment.
To edit the source code online, simply click the "Develop" button. The online code editor that appears is your personal development environment in the cloud that only you have ever access to. It is based on the popular open source [VS-Code](https://code.visualstudio.com/) editor.

Code editing is based on the git workflow which is the industry standard way for creating maintainable and auditable code for collaborative development. This means every change you make to the code is only present in your personal environment until you "commit" and "push" your code to the "master" branch of your application.

You can build and run your code **on a remote device (!)** during development using the side menu buttons. You need the "Develop" privilege on the device to use it in the code editor development context.

Using the terminal in the side menu you can log into a running app container directly on a device which is often useful for debugging on a device. The terminal from the side menu is not the same as the terminal accessible via the code editor's menu:

- The **side-menu-terminal** logs into the app container on a remote device.
- The **code-editor-terminal** logs into your development container in the cloud that runs the code editor and contains your clone of the git repository of the app.

> The side-menu-terminal used to access a remote device needs no open ports on the device.


### Interface with GitHub/GitLab/Bitbucket and your local editor
<style>
    img {
        margin: 12px;

    }
</style>
<img src="https://storage.googleapis.com/reswarm-images/GitHub-Mark-64px.png"/>
<img src="https://storage.googleapis.com/reswarm-images/gitlab.png" width="65"/>
<img src="https://storage.googleapis.com/reswarm-images/bitbucket.png" width="70"/>

Each app has a central Git repository that is used as the common code point for all developers of this app. By default this central Git repository is fully managed within IronFlock.
When you create an app you can choose to use another service instead. Currently the Git services from GitHub, GitLab and Bitbucket are supported.
For external Git repositories you need a "Personal Access Token" from the service to authenticate yourself. You can add these tokens in your IronFlock User Profile.

> In the application settings you can migrate an internal repository to one of those external services at any time later.

This way you can use your own local editor setup and push to your repo at GitHub. You can still use the online editor in IronFlock as before to run and debug the code on actual devices.

## Application Edge User Interface
What kind of user interface you want to provide for your app depends very much on the type of app you are developing. Some apps don't need any user input, some just require a simple form (see "Application Parameters" below) and some require a sophisticated web UI.

If you want to provide a custom user interface to the users of your app, you have to include a web server into your application that serves a web frontend to users.
Since the application will run on the users edge devices, which might be street lamps or machines in a production line, the web interface will normally not be accessible through the internet.
The platform however provides a secure tunneling service, which you can use to access the edge device's Web UI from remote.
To enable this external access all you have to do is add a `port-template.yml` file to your `.ironflock` folder and specify the ports on which your web server is serving the user frontend.
This information can then be used by the IronFlock tunnel service to open and close secure tunnels to your device.

<img src="https://storage.googleapis.com/reswarm-images/prod/rendered_port_template.png" height="200" style="margin-left: auto; margin-right: auto; margin-bottom: 16px; display: block;">

A privileged user can then enable and disable the tunnel for web access to a device at the settings icon of the running app on that device.

> Although a web interface can provide very sophisticated functionality to users, settings the user makes in an interface like that are always only valid for the single device the app runs on. You can however use Application Parameters for mass parametrization (see below) and an Application User Interface at the same time.

### Application Parameters
As an app developer you sometimes want to expose parameters to the user of the app without going through the effort of creating a complete web interface.
E.g. you build an app to collect data from a temperature sensor and you want the user of the app to be able to change the recording frequency. 

To expose application paramters to the user in a simple way, you can add a file `env-template.yml` to your `.ironflock` folder.
The contents of that file will be rendered as a nice form for users and will be accessible at the settings icon of the running app on a device or device group. 

> The default values you specify in the `env-template.yml` will be used when running the app during development.

<img src="https://storage.googleapis.com/reswarm-images/prod/rendered_template.png" height="300" style="margin-left: auto; margin-right: auto; margin-bottom: 16px; display: block;">

The user provided parameters will be available to your application as linux environment variables.

There are some standard environment variables that are always available in your application:

* **DEVICE_NAME**            current device's name (could change)
* **DEVICE_SERIAL_NUMBER**   the unique identifier of the device (is immutable)
* **SWARM_KEY**              the unique identifier of the device's fleet (could change)

With these environment variables your app can detect which device it is running on.

> Using Application Parameters the user can specify paramters for all devices in a group at once.
> Parameters can be provided by users even if the app is not running or a device is offline.

**Examples** where Application Parameters should be used are apps that run on many devices and where you want to specify a common target S3 bucket to push the data to. Or if you want to change model parameters for an AI-App on all devices at once.


**Examples** where you rather should provide your own web interface in the app are robot training software, Camera AI Setup or complex sensor hardware configuration software.

## Data Collection and Dashboards
Apps that run on edge devices usually produce data that should be collected centrally and be made accessible to users via dashboards.

<img src="https://storage.googleapis.com/reswarm-images/dashboard_demo.png" height="300" style="margin-left: auto; margin-right: auto; margin-bottom: 16px; display: block;"/>

In IronFlock you can bundle Dashboards and Data Stores into an App. When a user installs your App on a device in a fleet then this will also setup a private cloud data store in that fleet together with the dashboard that is automatically connected to this data store. In effect after installing an app on a device in a fleet the user can open a fully working dashboard presenting the data of his fleet devices the way the app developer intended.

### Cloud Data Collection
To provide your app with the data collection feature your app needs to publish data using the `publish_to_table` function of the `ironflock` SDK. ([ironflock-py](https://pypi.org/project/ironflock/) or [ironflock-js](https://www.npmjs.com/package/ironflock)).


Additionally you need to provide a `data-template.yml` file in the `.ironflock` folder of your app where you describe the data that is published by your app. With this information the IronFlock service can setup the necessary cloud database structures that will be private for every fleet (I.e a separate Database is used per fleet to collect timeseries data in the coud).

### Cloud Dashboards
Once you have set up the data store with a `data-template.yml` for your app it is very easy to create a dashboard as well. Just click the "Edit Dashboard" button in the side menu and the dashboard editor opens. Here you can add widgets and connect them to the data store. You can go back and forth and adjust the data store definition and the dashboard structure until you are satisfied. Note that the dashboard editor creates a `dashboard-template.yml` file in your `.ironflock` folder as well. You can also edit this file by hand if you like.

>It is perfectly fine for an app to just collect data and not provide a dashboard on its own. This is a common use case for data logger apps where dashboards will be created by the users themselves based on the collected data. User created dashboards can even use the data of multiple different apps in the same dashboard.

### Edge Data Volumes
If your app saves data on the device this data will normally not be retained accross app or device restarts.
To make your data persistant accross restarts, there are two folders you can use. These two folders are always mounted to the container when using a Dockerfile.

* **/data** A folder that is private to your app. Other apps can not access it's content.
* **/shared** A folder that is shared by all apps on the device.

If you are using docker compose instead, then you can configure your persisted volumes yourself.

## Releases and the App Store
If you want to make your app available to users, you can push the app to the central App Store, which supports private and public apps.

To create a release of an app you need to go to the "Releases" tab of the app's settings page.
There you need to choose a device for the publishing process. After you entered a version string in the version field and press "Publish"
the device builds and then publishes that app to your **private** App Store. The device you choose for the publishing process determines for which architecture the app will be published.
So if you choose an amd64 device, then the app will be available as an amd64 app in the App Store.
You can publish your app with multiple devices of different architectures to make the app available for multiple architectures at the same time.
Make sure to use the same version string for all architecture versions of your app to bundle them under one app version.



> If your app contains a data storage and dashboard configuration, then users will be able to access the app dashboard private to their fleet as soon as they installed your app. No further setup is required.

### Pricing Setup

If you want to **sell** your app to your private users or to the public, you can extend your account to a seller account and setup a pricing model for your app. In the settings section of the app page, you can provide the details. The usage of apps with a pricing model will be billed to the users monthly accross all users and devices.

### User Privileges
You can setup user privileges for your app in the "Privileges" tab of the app's settings page in the app studio.
There you can also invite other developers to collaborate with you on the app.

To make your app available in the globally public App Store you need to enable the "Public App Store" switch on the app's settings page in the Dev Studio.

> Your App release is _**not**_ automatically public. It can be installed by users only if you give them "Use" privileges unless you explicitely make it publicly available.


## Advanced Analytics

To receive data from an app running on a device and store it in a seperate analytics environment you can use the integrated [Data Studio](/pods). In this studio you can create a cloud database ("Data Pod") to collect data from the devices of a fleet. 

First you have to make sure the data pod owner has "Data Access" privileges for the fleet from which it should collect data. These privileges can be toggled in the fleet's settings.

Within your data pod you have to setup the fleet as a "Source" in the sources panel. When you activate the source, the data pod is actively listening for messages published from the devices of the fleet.

To send data from a device with your app you need to choose a "topic" in the code. (For details please refer to the documentation or look at the example app.)
Within your data pod you now create a raw table and enter that topic in it's settings. As soon as you activate the raw table the table will receive all data sent by the configured fleet's devices on this topic.

 >We provide a python library [ironflock-py](https://pypi.org/project/ironflock/) and a node.js library [ironflock-js](https://www.npmjs.com/package/ironflock). Please refer to the given links for further documentation. If you want to use other programming languages you can use the autobahn client libraries with the WAMP message protocol.

## Hardware access
Your app may want to interact with hardware like sensors that are attached to your device.
These devices are mounted into the `/dev` directory of your application container.

# LICENSE
### MIT
Copyright (c) 2021 Record Evolution GmbH
(See license file in the source code)