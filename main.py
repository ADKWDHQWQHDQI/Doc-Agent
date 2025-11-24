"""
Universal Documentation Agent - MVP
Main entry point for the application
"""

import sys
import argparse
from pathlib import Path

from config import Config
from orchestrator import DocumentationOrchestrator
import asyncio


async def main():
    """Main CLI interface (async)"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Universal Documentation Agent - Generate professional documentation using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate BRD from a prompt (auto-proceeds if clear)
  python main.py --request "Create a BRD for an e-commerce platform"
  
  # Ambiguous requests auto-trigger conversational mode
  python main.py --request "Generate documentation"  # Will ask clarifying questions
  
  # Generate technical documentation from code
  python main.py --request "Generate FRD" --code-dir ./my-project
  
  # Generate Cloud Implementation Guide
  python main.py --request "Create Azure deployment guide" --code-dir ./app --doc-type CLOUD
  
  # Analyze specific files
  python main.py --request "Document this API" --files api.py routes.py
        """
    )
    
    parser.add_argument(
        '--request', '-r',
        type=str,
        required=True,
        help='Your documentation request or prompt'
    )
    
    parser.add_argument(
        '--code-dir', '-c',
        type=str,
        help='Directory containing source code to analyze'
    )
    
    parser.add_argument(
        '--files', '-f',
        nargs='+',
        help='Specific files to analyze'
    )
    
    parser.add_argument(
        '--doc-type', '-t',
        type=str,
        choices=['BRD', 'FRD', 'NFRD', 'CLOUD', 'SECURITY', 'API'],
        help='Document type (optional, will be auto-detected if not specified)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Custom output file path'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet mode - minimal output (only errors and final result)'
    )
    
    parser.add_argument(
        '--full-preview',
        action='store_true',
        help='Show full document content instead of 500 char preview'
    )
    
    parser.add_argument(
        '--no-exit',
        action='store_true',
        help='Raise exceptions instead of sys.exit() (useful for testing/library use)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    validation_errors = []
    
    # Validate --files argument
    if args.files is not None:
        if not args.files or len(args.files) == 0:
            validation_errors.append("--files specified but no files provided")
        else:
            # Check if files exist
            missing_files = [f for f in args.files if not Path(f).exists()]
            if missing_files:
                validation_errors.append(f"Files not found: {', '.join(missing_files)}")
    
    # Validate --code-dir argument
    if args.code_dir:
        code_path = Path(args.code_dir)
        if not code_path.exists():
            validation_errors.append(f"Code directory not found: {args.code_dir}")
        elif not code_path.is_dir():
            validation_errors.append(f"Code path is not a directory: {args.code_dir}")
    
    # Validate --output argument
    if args.output:
        output_path = Path(args.output)
        if output_path.exists() and output_path.is_dir():
            validation_errors.append(f"Output path is a directory: {args.output}")
        # Check parent directory exists
        if not output_path.parent.exists():
            validation_errors.append(f"Output directory does not exist: {output_path.parent}")
    
    # Report validation errors
    if validation_errors:
        print("❌ Argument Validation Errors:")
        for i, error in enumerate(validation_errors, 1):
            print(f"   {i}. {error}")
        print("\n💡 Use --help for usage information")
        sys.exit(1) if not args.no_exit else None
        if args.no_exit:
            raise ValueError(f"Argument validation failed: {validation_errors}")
    
    # Validate configuration
    try:
        if not Config.validate():
            raise ValueError("Configuration validation failed")
    except (ValueError, AttributeError) as e:
        if not args.quiet:
            print(f"❌ Configuration Error: {e}")
            print("\n💡 Setup Instructions:")
            print("1. Copy .env.example to .env")
            print("2. Fill in your Azure OpenAI credentials:")
            print("   - AZURE_OPENAI_ENDPOINT")
            print("   - AZURE_OPENAI_API_KEY")
            print("   - AZURE_OPENAI_DEPLOYMENT_NAME (e.g., gpt-4o)")
            print("\nFor more information, see README.md")
        if args.no_exit:
            raise
        sys.exit(1)
    
    # Display banner (unless quiet mode)
    if not args.quiet:
        print("=" * 70)
        print("   UNIVERSAL DOCUMENTATION AGENT - MVP")
        print("   Powered by Azure OpenAI & Multi-Agent Architecture")
        print("=" * 70)
        print()
    
    # Initialize orchestrator
    orchestrator = DocumentationOrchestrator()
    
    # Append doc type to request if specified
    request = args.request
    if args.doc_type:
        request = f"Generate a {args.doc_type} document: {request}"
    
    # Generate documentation with auto-trigger conversational mode
    # System automatically detects ambiguous requests and launches conversation
    result = await orchestrator.generate_documentation_async(
        user_request=request,
        code_directory=args.code_dir,
        input_files=args.files
    )
    
    # Process results
    try:
        # Validate result is a dictionary
        if not isinstance(result, dict):
            print(f"\n❌ Unexpected result type: {type(result)}")
            print(f"Result: {result}")
            sys.exit(1)
        
        # Check for error status
        if result.get('status') == 'error':
            print("\n❌ Error during generation:")
            print(f"   {result.get('message', 'Unknown error')}")
            sys.exit(1)
        
        # Handle clarification request (from non-interactive mode)
        if result.get('status') == 'needs_clarification':
            if not args.quiet:
                print("=" * 70)
                print("❓ More Information Needed")
                print("=" * 70)
                print("\n✨ The system needs clarification to proceed.")
                print("   Please provide more details and try again.")
                print("\n💡 Tip: Use --interactive (-i) mode for guided conversation\n")
            if args.no_exit:
                return result
            sys.exit(0)
        
        # Handle multi-document generation
        if result.get('status') == 'success' and 'documents' in result:
            if not args.quiet:
                print("=" * 70)
                print("✅ Multi-Document Generation Complete!")
                print("=" * 70)
                print(f"\n📦 Total Documents: {result.get('total_documents', len(result.get('documents', [])))}")
                print(f"📄 Documents Generated:")
                for doc in result.get('documents', []):
                    doc_type = doc.get('document_type', 'UNKNOWN')
                    output_path = doc.get('output_path', 'unknown')
                    print(f"   - {doc_type}: {Path(output_path).name}")
                
                summary_path = result.get('summary_path')
                if summary_path:
                    print(f"\n📋 Package Summary: {Path(summary_path).name}")
                print("\n✨ Thank you for using Universal Documentation Agent!")
            if args.no_exit:
                return result
            sys.exit(0)
        
        # Validate required keys for single document
        required_keys = ['document', 'output_path', 'document_type', 'workflow']
        missing_keys = [key for key in required_keys if key not in result]
        if missing_keys and not args.quiet:
            print(f"\n⚠️  Warning: Result missing keys: {missing_keys}")
            print("\nAttempting to display available information...\n")
        
        # Display single document results
        if not args.quiet:
            print("=" * 70)
            print("✅ Documentation Generation Complete!")
            print("=" * 70)
            print(f"\n📄 Document Type: {result.get('document_type', 'UNKNOWN')}")
            print(f"📁 Output Path: {result.get('output_path', 'unknown')}")
            print(f"🔄 Workflow Used: {result.get('workflow', 'unknown')}")
        
        # Display document preview if available
        document_content = result.get('document', '')
        if document_content and not args.quiet:
            print("\n" + "=" * 70)
            if args.full_preview:
                print("📋 DOCUMENT CONTENT (Full)")
                print("=" * 70)
                print(str(document_content))
            else:
                print("📋 DOCUMENT PREVIEW (First 500 characters)")
                print("=" * 70)
                preview = str(document_content)[:500]
                print(preview)
                if len(str(document_content)) > 500:
                    print("\n... (truncated)")
                    print("\n💡 Use --full-preview to see complete document")
            print()
        elif not document_content and not args.quiet:
            print("\n⚠️  Warning: No document content in result")
        
        # Save workflow log if available
        workflow_log = result.get('log', []) if isinstance(result, dict) else []
        if workflow_log and not args.quiet:
            try:
                log_path = Config.OUTPUT_DIR / f"workflow_log_{orchestrator._get_timestamp()}.txt"
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write("WORKFLOW LOG\n")
                    f.write("=" * 70 + "\n\n")
                    for entry in workflow_log:
                        f.write(f"Step: {entry.get('step', 'unknown')}\n")
                        f.write(f"Time: {entry.get('timestamp', 'unknown')}\n")
                        data = entry.get('data', {})
                        # Truncate large data for log file
                        if isinstance(data, dict):
                            for key, value in data.items():
                                value_str = str(value)[:500] if len(str(value)) > 500 else str(value)
                                f.write(f"  {key}: {value_str}\n")
                        else:
                            f.write(f"Data: {str(data)[:500]}\n")
                        f.write("-" * 70 + "\n\n")
                
                if not args.quiet:
                    print(f"📊 Workflow log saved to: {log_path}")
            except Exception as log_error:
                if not args.quiet:
                    print(f"⚠️  Could not save workflow log: {log_error}")
        elif not workflow_log and not args.quiet:
            print("ℹ️  No workflow log available")
        
        if not args.quiet:
            print("\n✨ Thank you for using Universal Documentation Agent!")
        
        # Return result for library/testing use
        if args.no_exit:
            return result
        
    except KeyboardInterrupt:
        if not args.quiet:
            print("\n\n⚠️  Process interrupted by user")
        if args.no_exit:
            raise
        sys.exit(0)
    except KeyError as e:
        if not args.quiet:
            print(f"\n❌ Result format error - missing key: {e}")
            print("\nThis might indicate an issue with the orchestration workflow.")
            print(f"Available result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        if args.no_exit:
            raise
        sys.exit(1)
    except TypeError as e:
        if not args.quiet:
            print(f"\n❌ Type error during result processing: {e}")
            print(f"Result type: {type(result)}")
        if args.no_exit:
            raise
        sys.exit(1)
    except Exception as e:
        if not args.quiet:
            print(f"\n❌ Error during documentation generation: {str(e)}")
            print(f"\nError type: {type(e).__name__}")
            print("\n💡 Troubleshooting:")
            print("- Check your Azure OpenAI credentials in .env")
            print("- Ensure you have sufficient quota/credits")
            print("- Verify network connectivity")
            print("- Check the error message above for details")
            
            # Debug information
            if '--debug' in sys.argv or '-d' in sys.argv:
                import traceback
                print("\n🐛 Debug Information:")
                traceback.print_exc()
        
        if args.no_exit:
            raise
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
