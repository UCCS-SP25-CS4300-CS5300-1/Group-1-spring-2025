self.addEventListener('push', function(event) {
    console.log("Push event received");

    let data = {};

    if (event.data) {
        try {
            data = event.data.json(); 
            console.log("Parsed push data as JSON:", data);
        } catch (e) {
            console.warn("Push data is not JSON. Falling back to text. Error:", e);
            data = {
                head: "Notification",
                body: event.data.text()
            };
        }
    }

    const promiseChain = Promise.resolve(data.body).then(bodyText => {
        const title = data.head || "To-Do Reminder";
        const options = {
            body: bodyText || "You have a task due!",
            data: {
                url: data.url || "/"
            }
        };
        return self.registration.showNotification(title, options);
    });

    event.waitUntil(promiseChain);
});

self.addEventListener('notificationclick', function(event) {
    console.log("Notification clicked");
    event.notification.close();

    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});
