# IronFlock Integration

This folder contains the (optional) integration of your app with the IronFlock platform.
Integrating your app with the IronFlock platform allows your app to leverage different features, the platform provides:

- data collection
- dashboarding
- remote access
- app parametrization and mass parametrization


## Data Collection

If your app should collect data from multiple devices into a central data store you can use the IronFlock data infrastructure. To set up a data collection backend for your app you need to provide a `data-template.yml` in this folder.

When a user installs your app on a device in his/her fleet then this will also setup a cloud data store privately for that fleet. Additionally a private message routing realm (unified name space) is created for this app and fleet. This architecture guarantees that your app's data is securly handled in each user's private fleet infrastrucutre. 

> The user has full control over the data collected by your app in his/her fleet and you as the developer will not have access to this data!

Once you set up your table structure with the `data-template.yml` your app can start publishing data to these tables. To do this your app needs to use the `publish_to_table` function of the `ironflock` SDK. ([ironflock-py](https://pypi.org/project/ironflock/) or [ironflock-js](https://www.npmjs.com/package/ironflock)).


## Dashboarding

If you want to provide a real-time dashboard together with your app, that shows data from all devices in a fleet, you can setup an app dashboard.

<img src="https://storage.googleapis.com/reswarm-images/dashboard_demo.png" height="300" style="margin-left: auto; margin-right: auto; margin-bottom: 16px; display: block;"/>

The configuration of the app dashboard is stored in the `dashboard-template.yml` in this folder. To populate the dashboard-template.yml there is a dashboard editor that you can start by clicking on the dashboard button in the sidebar.

> You can also manually change settings of the dashboard in the `dashboard-template.yml`.

In the dashboard editor you add and configure each widget and hook up the widget with the underlying data that has been configured in the `data-template.yml`.

Just as with the data collection integration above, when a user installs your app on a fleet, the user will always see the data of his/her fleet in the dashboard.

> In effect, if the user installs your app on his/her fleet, he/she can immediately open your dashboard and look at the real-time and historical data of his/her fleet. No further data infrastructure and messaging setup is required by you or the user.

## Remote Access

If your app should be accessible remotely when running on individual devices, you can configure the integration of your app with the secure IronFlock remote access infrastructure.

You simply need to provide a `port-template.yml` that details the ports and protocols that should be available for remote access.

> Configuring remote access information in the `port-template.yml` does NOT activate remote access! Only privileged users can control remote access on their devices.

Once you provided the necessary information in the `port-template.yml` the users of your app can enable or disable remote access, depending on the networking privileges the user has in his/her fleet.

### Example:
You device provides a HMI (Human Machine Interface) as web interface to configure machine settings. This web interface is served as a web site by your app on a specific port. If you enter the port name in the `port-template.yml` the IronFlock remote access infrastructure can set up a reverse proxy tunnel so that users can access the HMI with a browser from the internet. Only privileged users of the fleet using your app can control remote access activation/deactivation on devices.

> Every activation and deactivation of a remote access tunnel is logged by IronFlock and can be inspected in the audit log panel of the device. Each actual usage of an activated remote access tunnel is logged there as well.

Remote access is not limited to web access. You can use Remote Desktop (VNC) or setup a VPN (via UDP) or plain tcp/ip access. The IronFlock remote access infrastructure can tunnel each of these protocolls.

This enables different remote access use cases:

- remote PLC programming with Siemens TIA portal, Codesys, TwinCat, etc...
- remote HMI for machine configuration
- remote Monitoring for realtime machine inspection
- realtime video streaming

## App Parameters

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
