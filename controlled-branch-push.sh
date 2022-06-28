#!/bin/bash

check_branch_name() {
    local branch_to_check=$1
    current_branch=$(git branch | grep '* ' | awk '{print $2}')
    if [ $current_branch = $branch_to_check ]; then
      echo "Cancelling push to restricted $branch_to_check"
      echo "To force direct push to $current_branch use:"
      echo "  SKIP=push-check git push"
      exit 2
    fi
}

check_branch_name acceptance

exit