#!/bin/bash
echo "Packaging AWS Lambda Layer with dependencies"
zip -r thasus-lib.zip ./python
echo "Done packaging"