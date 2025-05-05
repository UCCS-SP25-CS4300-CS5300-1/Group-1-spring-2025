self.addEventListener('push', function(event) {
    console.log("Push event received");

    let data = {};
    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            console.error("Error parsing push data from stf1:", e);
            try {
                data = {
                    head: "Notification",
                    body: event.data.text()
                };
            } catch (textError) {
                console.error("Error reading push text data:", textError);
                data = {
                    head: "Notification",
                    body: "You have a task due!"
                };
            }
        }
    }

    const title = data.head || "To-Do Reminder";
    const options = {
        body: data.body || "You have a task due!",
        data: {
            url: data.url || "/"
        }
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    console.log("Notification clicked");
    event.notification.close();

    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});
