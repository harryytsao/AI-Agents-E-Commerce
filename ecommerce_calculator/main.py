import os
import logging
import json
from datetime import datetime
from ecommerce_calculator.handlers.request_handlers import process_ecommerce_request
from ecommerce_calculator.utils.logging import setup_logging
from uuid import UUID

def main():
    """Main function to run different test scenarios"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("\nEcommerce Calculator Test Suite")
    print("--------------------------------")
    
    while True:
        print("\nSelect a test to run:")
        print("1. Test Product Lifecycle Analysis")
        print("2. Test Product Seasonality Analysis")
        print("3. Test Product Demand Analysis")
        print("4. Test Invalid Request")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-4): ")
        product_id = input("\nEnter the product ID: ").strip()
        
        if not product_id:
            print("\nError: Product ID cannot be empty")
            continue
            
        try:
            # Validate UUID format
            UUID(product_id)
        except ValueError:
            print("\nError: Invalid UUID format. Please enter a valid product ID")
            continue

        if choice == "1":
            print("\nTesting lifecycle analysis...")
            test_input = f"What's the lifecycle stage for product {product_id}?"
            print(f"Test input: {test_input}")
            result = process_ecommerce_request(test_input)
            
        elif choice == "2":
            print("\nTesting seasonality analysis...")
            test_input = f"Is product {product_id} seasonal?"
            print(f"Test input: {test_input}")
            result = process_ecommerce_request(test_input)
            
        elif choice == "3":
            print("\nTesting demand analysis...")
            test_input = f"What's the demand forecast for product {product_id} between 2024-01-01 and 2024-12-31?"
            print(f"Test input: {test_input}")
            result = process_ecommerce_request(test_input)
            
        elif choice == "4":
            print("\nTesting invalid request...")
            test_input = "What's the weather like today?"
            print(f"Test input: {test_input}")
            result = process_ecommerce_request(test_input)
            
        elif choice == "0":
            print("\nExiting...")
            break
            
        else:
            print("\nInvalid choice. Please try again.")
            continue
        
        if result:
            print(f"\nSuccess: {result.success}")
            print(f"Message: {result.message}")
            if result.analysis_data:
                print("\nAnalysis Data:")
                print(json.dumps(result.analysis_data, indent=2))
        else:
            print("\nNo response received")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 