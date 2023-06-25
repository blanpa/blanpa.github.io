---
title: 4th week of the MLOps Zoom Camp
tags: [mlobs, zoomcamp, prefect]
style: fill
color: light
description: 4th week of the MLOps Zoom Camp
---

🚀 Exciting developments in the 4th week of the MLOps Zoom Camp!

https://github.com/DataTalksClub/mlops-zoomcamp/tree/main/04-deployment

This week, we dived into the world of Deployment and explored various strategies to bring our trained models to life. Let's do a quick recap of what we covered.

In our previous sessions, we learned how to transform our training process into a well-defined workflow. Now, it's time to understand how to deploy our resulting models effectively.

During this week, we focused on two paradigms of deployment: Batch Deployment (Offline) and Online Deployment. Let's take a closer look at each of them.

1️⃣ Batch Deployment, Offline:
This approach is suitable when we can afford to wait a bit for predictions. It involves setting up a database and a scoring job. Periodically, the scoring job pulls new data from the database and runs our trained model on it. The resulting predictions are then stored in a predictions database. An excellent example of batch deployment is the churn job, where we periodically predict the likelihood of customer churn.

2️⃣ Online Deployment:
When we need immediate predictions, we turn to online deployment options. Here, we have two primary methods:

Web Service:
In this scenario, our model is always available for prediction. For instance, think of our taxi duration prediction app. When the backend sends data to the model, it responds promptly with the predicted duration. The relationship between the client (backend) and the model is one-to-one, ensuring quick predictions for real-time applications.

Streaming:
Streaming deployment involves a producer(s) and consumers. The producer pushes data into a data stream, and the consumers consume the data for prediction. With streaming, we can have multiple consumers predicting different variables from the same data stream. For example, when a ride starts, the backend (producer) pushes the data into the stream, and consumer 1 predicts the duration, consumer 2 predicts the cost, consumer 3 predicts the tip, and so on.

We also explored the possibility of combining these approaches. For instance, we can run a simple model as a web service with the backend. If the user agrees, we can push the data to the stream with an associated event, triggering a more accurate prediction model (e.g., consumer 1) to run and provide an enhanced duration prediction. This flexibility allows us to cater to specific use cases efficiently.

Furthermore, consumers can push their predictions to a prediction stream, and a decision service can act upon them, enabling intelligent decision-making based on the predicted outcomes.

Exciting times ahead as we continue our journey through the MLOps Zoom Camp! Stay tuned for more insights and practical hands-on experiences. Let's keep pushing the boundaries of deployment to ensure our models make a real impact in the world.

#MLOps #Deployment #DataScience #MachineLearning #ArtificialIntelligence