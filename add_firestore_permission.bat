@echo off
echo Adding Firestore permissions to aiden.kim@ggproduction.net...

gcloud projects add-iam-policy-binding gg-poker-prod ^
  --member="user:aiden.kim@ggproduction.net" ^
  --role="roles/datastore.user"

echo.
echo Done! Firestore permissions added.
echo Please wait 1-2 minutes for permissions to propagate.
