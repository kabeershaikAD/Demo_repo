"""
Build Comprehensive Indian Legal Database
This script builds a massive Indian legal database using Indian Kanoon API.
"""
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from indian_kanoon_api import IndianKanoonAPI
from indian_legal_database import IndianLegalDatabase
from enhanced_app import EnhancedAgenticLegalRAG


class IndianLegalDatabaseBuilder:
    """Builder for comprehensive Indian legal database."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Initialize components
        self.kanoon_api = IndianKanoonAPI(config)
        self.legal_database = IndianLegalDatabase(config)
        self.enhanced_rag = EnhancedAgenticLegalRAG(config)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # Build statistics
        self.build_stats = {
            "start_time": None,
            "end_time": None,
            "total_documents": 0,
            "judgments": 0,
            "acts": 0,
            "errors": 0,
            "sources": {}
        }
        
    def setup_logging(self):
        """Setup logging for the database builder."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        builder_logger = logging.getLogger("database_builder")
        builder_logger.setLevel(logging.INFO)
        
        file_handler = logging.FileHandler(log_dir / "database_builder.log")
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        builder_logger.addHandler(file_handler)
        self.logger = builder_logger
    
    async def build_comprehensive_database(self, max_documents_per_type: int = 2000):
        """Build a comprehensive Indian legal database."""
        try:
            self.build_stats["start_time"] = datetime.now()
            self.logger.info(f"Starting comprehensive database build with {max_documents_per_type} documents per type...")
            
            # Step 1: Get all legal data from Indian Kanoon
            print("🔍 Fetching legal data from Indian Kanoon...")
            self.logger.info("Fetching legal data from Indian Kanoon...")
            
            documents = await self.kanoon_api.get_all_legal_data(max_documents_per_type)
            
            print(f"✅ Fetched {len(documents)} documents from Indian Kanoon")
            self.logger.info(f"Fetched {len(documents)} documents from Indian Kanoon")
            
            # Step 2: Convert and categorize documents
            print("📝 Processing and categorizing documents...")
            self.logger.info("Processing and categorizing documents...")
            
            legal_docs = []
            judgments = 0
            acts = 0
            
            for doc in documents:
                legal_doc = {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "content": doc.content,
                    "doc_type": doc.doc_type,
                    "court": doc.court,
                    "date": doc.date,
                    "url": doc.url,
                    "source": "Indian Kanoon",
                    "citations": doc.citations,
                    "keywords": doc.keywords,
                    "hash": doc.hash
                }
                legal_docs.append(legal_doc)
                
                if doc.doc_type == "judgment":
                    judgments += 1
                elif doc.doc_type == "act":
                    acts += 1
            
            self.build_stats["judgments"] = judgments
            self.build_stats["acts"] = acts
            self.build_stats["total_documents"] = len(legal_docs)
            
            print(f"📊 Document Statistics:")
            print(f"   - Total Documents: {len(legal_docs)}")
            print(f"   - Judgments: {judgments}")
            print(f"   - Acts: {acts}")
            
            # Step 3: Save to database
            print("💾 Saving documents to database...")
            self.logger.info("Saving documents to database...")
            
            added = self.legal_database.save_documents(legal_docs)
            
            print(f"✅ Saved {added} documents to database")
            self.logger.info(f"Saved {added} documents to database")
            
            # Step 4: Initialize RAG system
            print("🤖 Initializing RAG system...")
            self.logger.info("Initializing RAG system...")
            
            await self.enhanced_rag.initialize()
            
            # Step 5: Add documents to vector database
            print("🔍 Building vector database...")
            self.logger.info("Building vector database...")
            
            await self.enhanced_rag._add_documents_to_rag(legal_docs)
            
            print("✅ Vector database built successfully")
            self.logger.info("Vector database built successfully")
            
            # Step 6: Start dynamic monitoring
            print("🔄 Starting dynamic monitoring...")
            self.logger.info("Starting dynamic monitoring...")
            
            await self.enhanced_rag.start_monitoring()
            
            print("✅ Dynamic monitoring started")
            self.logger.info("Dynamic monitoring started")
            
            # Step 7: Generate build report
            self.build_stats["end_time"] = datetime.now()
            build_report = self.generate_build_report()
            
            print("\n🎉 Database build completed successfully!")
            print(f"📊 Build Report:")
            print(json.dumps(build_report, indent=2))
            
            # Save build report
            with open("build_report.json", "w") as f:
                json.dump(build_report, f, indent=2)
            
            self.logger.info("Database build completed successfully")
            
            return build_report
            
        except Exception as e:
            self.logger.error(f"Error building database: {e}")
            print(f"❌ Error building database: {e}")
            return {"error": str(e)}
    
    def generate_build_report(self) -> Dict:
        """Generate comprehensive build report."""
        try:
            # Get database statistics
            db_stats = self.legal_database.get_database_stats()
            
            # Calculate build time
            if self.build_stats["start_time"] and self.build_stats["end_time"]:
                build_duration = (self.build_stats["end_time"] - self.build_stats["start_time"]).total_seconds()
            else:
                build_duration = 0
            
            # Get system status
            system_status = asyncio.run(self.enhanced_rag.get_system_status())
            
            report = {
                "build_info": {
                    "start_time": self.build_stats["start_time"].isoformat() if self.build_stats["start_time"] else None,
                    "end_time": self.build_stats["end_time"].isoformat() if self.build_stats["end_time"] else None,
                    "duration_seconds": build_duration,
                    "duration_minutes": build_duration / 60,
                    "duration_hours": build_duration / 3600
                },
                "document_statistics": {
                    "total_documents": self.build_stats["total_documents"],
                    "judgments": self.build_stats["judgments"],
                    "acts": self.build_stats["acts"],
                    "documents_added_to_db": db_stats.get("total_documents", 0),
                    "recent_documents": db_stats.get("recent_documents", 0)
                },
                "database_info": {
                    "total_documents": db_stats.get("total_documents", 0),
                    "document_types": db_stats.get("document_types", {}),
                    "courts": db_stats.get("courts", {}),
                    "sources": db_stats.get("sources", {}),
                    "database_size_bytes": db_stats.get("database_size", 0),
                    "database_size_mb": db_stats.get("database_size", 0) / (1024 * 1024)
                },
                "system_status": system_status,
                "build_success": True,
                "timestamp": datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating build report: {e}")
            return {
                "build_success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_system(self):
        """Test the built system with sample queries."""
        try:
            print("\n🧪 Testing the built system...")
            self.logger.info("Testing the built system...")
            
            # Test queries
            test_queries = [
                "What is the definition of invention under patent law?",
                "What are the requirements for patentability?",
                "Can living organisms be patented?",
                "What is the latest Supreme Court judgment on Aadhaar?",
                "What are the provisions of Section 377?",
                "What is the right to privacy in Indian Constitution?",
                "What are the fundamental rights under Article 19?",
                "What is the procedure for filing a patent application?",
                "What are the grounds for divorce under Hindu Marriage Act?",
                "What is the punishment for cyber crimes under IT Act?"
            ]
            
            results = []
            
            for i, query in enumerate(test_queries, 1):
                print(f"   Testing query {i}/{len(test_queries)}: {query[:50]}...")
                
                try:
                    result = await self.enhanced_rag.process_query(query)
                    results.append({
                        "query": query,
                        "success": "error" not in result,
                        "answer_length": len(result.get("answer", "")),
                        "citations": len(result.get("citations", [])),
                        "confidence": result.get("confidence", 0)
                    })
                    
                    if "error" in result:
                        print(f"      ❌ Error: {result['error']}")
                    else:
                        print(f"      ✅ Success: {len(result.get('answer', ''))} chars, {len(result.get('citations', []))} citations")
                        
                except Exception as e:
                    print(f"      ❌ Exception: {e}")
                    results.append({
                        "query": query,
                        "success": False,
                        "error": str(e)
                    })
            
            # Calculate test statistics
            successful_queries = sum(1 for r in results if r.get("success", False))
            total_queries = len(results)
            success_rate = (successful_queries / total_queries) * 100 if total_queries > 0 else 0
            
            print(f"\n📊 Test Results:")
            print(f"   - Total Queries: {total_queries}")
            print(f"   - Successful: {successful_queries}")
            print(f"   - Success Rate: {success_rate:.1f}%")
            
            # Save test results
            test_report = {
                "test_timestamp": datetime.now().isoformat(),
                "total_queries": total_queries,
                "successful_queries": successful_queries,
                "success_rate": success_rate,
                "results": results
            }
            
            with open("test_results.json", "w") as f:
                json.dump(test_report, f, indent=2)
            
            self.logger.info(f"System test completed: {successful_queries}/{total_queries} queries successful")
            
            return test_report
            
        except Exception as e:
            self.logger.error(f"Error testing system: {e}")
            print(f"❌ Error testing system: {e}")
            return {"error": str(e)}


async def main():
    """Main function for building the Indian legal database."""
    print("🏛️ Indian Legal Database Builder")
    print("=" * 50)
    
    # Initialize builder
    builder = IndianLegalDatabaseBuilder()
    
    # Build comprehensive database
    print("Starting comprehensive database build...")
    build_report = await builder.build_comprehensive_database(max_documents_per_type=1000)
    
    if "error" not in build_report:
        # Test the system
        test_report = await builder.test_system()
        
        print("\n🎉 Build and test completed successfully!")
        print(f"📁 Build report saved to: build_report.json")
        print(f"📁 Test results saved to: test_results.json")
        
        # Show final statistics
        print(f"\n📊 Final Statistics:")
        print(f"   - Total Documents: {build_report['document_statistics']['total_documents']}")
        print(f"   - Judgments: {build_report['document_statistics']['judgments']}")
        print(f"   - Acts: {build_report['document_statistics']['acts']}")
        print(f"   - Database Size: {build_report['database_info']['database_size_mb']:.2f} MB")
        print(f"   - Build Time: {build_report['build_info']['duration_minutes']:.2f} minutes")
        
        if "test_results" in locals():
            print(f"   - Test Success Rate: {test_report['success_rate']:.1f}%")
        
        print(f"\n🚀 System is ready for use!")
        print(f"   - Run 'streamlit run ui.py' to start the web interface")
        print(f"   - Run 'python enhanced_app.py' to use the API")
        print(f"   - Dynamic updates are running automatically")
        
    else:
        print(f"❌ Build failed: {build_report['error']}")


if __name__ == "__main__":
    asyncio.run(main())






















