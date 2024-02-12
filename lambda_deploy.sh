#!/bin/bash
echo "Build and Deploy Thasus Lambda Function to AWS"

echo "Packaging"
rm -rf thasus.zip
zip -r thasus.zip . -x "./.idea/*" "./python/*" "./*.zip" "./latest_run.log" "./.gitignore" "./.git/*" "./venv/*" "./thasus/persistence/credentials.py"
echo "Packaging complete"
echo "Deploying Thasus to AWS"
aws lambda update-function-code --function-name thasus --zip-file fileb:///mnt/e/IntelliJ/thasus/thasus.zip --publish --profile thasus_cli --region us-west-2
echo "Thasus deployment complete"
echo "Running Thasus in Lambda"
sleep 5
aws lambda invoke --profile thasus_cli --function-name thasus --payload fileb://test_event.json latest_run.log --region us-west-2
cat latest_run.log
echo ""
echo "Done"
