from pathlib import Path
import sqlite3
from typing import Dict

from flask import Flask, jsonify
from flask_cors import CORS


class DatabaseManager:
    def __init__(self, db_path: str = "promptrace.db"):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}")
    
    def get_connection(self):
        return sqlite3.connect(str(self.db_path))
    
    def dict_factory(self, cursor: sqlite3.Cursor, row: tuple) -> Dict:
        """Convert database row to dictionary"""
        fields = [column[0] for column in cursor.description]
        return {key: value for key, value in zip(fields, row)}

class StudioApi:

    SELECT_EXPERIMENTS_QUERY = """
                                SELECT
                                e.experiment_id,
                                json_extract(model, '$.type') AS model_type,
                                json_extract(model, '$.api_version') AS model_api_version,
                                json_extract(model, '$.endpoint') AS model_endpoint,
                                json_extract(model, '$.inference_model_deployment') AS inference_model_deployment,
                                json_extract(model, '$.embedding_model_deployment') AS embedding_model_deployment,
                                json_extract(asset, '$.prompt_template_id') AS prompt_template_id,
                                json_extract(asset, '$.dataset_id') AS dataset_id,
                                er.dataset_record_id as dataset_record_id,
                                er.inference as inference,
                                er.prompt_tokens as prompt_tokens,
                                er.completion_tokens as completion_tokens,
                                er.latency_ms as latency_ms,
                                er.evaluation as evaluation  
                                FROM experiments e
                                JOIN experiment_result er on e.experiment_id = er.experiment_id 
                                """

    # SELECT_EXPERIMENTS_QUERY = """
    #                     SELECT 
    #                         experiment_id,
    #                         model_type,
    #                         model_api_version,
    #                         model_endpoint,
    #                         model_deployment,                               
    #                         prompt_template_path,
    #                         system_prompt_template,
    #                         user_prompt_template,                               
    #                         dataset_path,
    #                         dataset_record_id,
    #                         inference,
    #                         prompt_tokens,
    #                         completion_tokens,
    #                         latency_ms,
    #                         evaluation,
    #                         created_at                      
    #                     FROM experiments 
    #                 """
    
    def __init__(self, db_path: str = "promptrace.db"):
        self.app = Flask(__name__)
        CORS(self.app, resources={r"/*": {"origins": "*"}})
        self.db = DatabaseManager(db_path)
        self._setup_routes()
        
    def _setup_routes(self):
        @self.app.route("/experiments", methods=["GET"])
        def get_experiments():
            try:
                with self.db.get_connection() as conn:
                    conn.row_factory = self.db.dict_factory
                    cursor = conn.cursor()
                    
                    cursor.execute(self.SELECT_EXPERIMENTS_QUERY)
                    
                    experiments = cursor.fetchall()                    
                    
                    return jsonify({                        
                            "experiments": experiments                       
                    })
                    
            except sqlite3.Error as e:
                return jsonify({
                    "status": "error",
                    "message": "Database error occurred",
                    "error": str(e)
                }), 500
                
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error": str(e)
                }), 500
    
    def run(self, host: str = "127.0.0.1", port: int = 5000):
        self.app.run(host=host, port=port)

