#!/bin/bash
echo "Build and Deploy Thasus Lambda Function to AWS"

echo "Packaging"
cd /Users/farhan.syed/farhan/scraper/thasus/
rm -rf thasus.zip
zip -r thasus.zip . -x "./.idea/*" "./python/*" "./thasus-lib.zip" "./latest_run.log" "./.gitignore" "./.git/*"
echo "Packaging complete"
echo "Deploying Thasus to AWS"
aws lambda update-function-code --function-name thasus --zip-file fileb:///Users/farhan.syed/farhan/scraper/thasus/thasus.zip --publish --profile cadmus_cli
echo "Thasus deployment complete"
echo "Running Thasus in Lambda"
sleep 5
aws lambda invoke --profile cadmus_cli --function-name thasus --payload fileb://test_event.json latest_run.log
cat latest_run.log
echo ""
echo "Done"
