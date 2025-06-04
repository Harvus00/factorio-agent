from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import Dict, List
import json
import os

class DocProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        # for long text
        self.long_text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size * 2,  # longer chunk size
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    def _split_text_with_metadata(self, text: str, metadata: Dict, type: str, name: str) -> List[Dict]:
        """split text with metadata"""
        if len(text) <= self.text_splitter._chunk_size:
            return [{
                "type": type,
                "name": name,
                "content": text,
                "metadata": metadata
            }]
        # if text is too long, use longer chunk size to split
        chunks = self.long_text_splitter.split_text(text)
        return [{
            "type": type,
            "name": name,
            "content": chunk,
            "metadata": metadata
        } for chunk in chunks]

    def process_api_doc(self, api_json: Dict) -> List[Dict]:
        chunks = []
        # Process classes
        for class_data in api_json.get("classes", {}):
            # Process class description
            class_text = f"Class: {class_data.get('name')}\nDescription: {class_data.get('description', '')}"
            class_metadata = {
                "class_name": class_data.get('name'),
                "parent_class": class_data.get("parent")
            }
            chunks.extend(self._split_text_with_metadata(
                class_text, 
                class_metadata,
                "class",
                class_data.get('name')
            ))

            # Process methods
            for method_data in class_data.get("methods", {}):
                method_text = self._format_method_text(class_data.get('name'), method_data.get('name'), method_data)
                method_metadata = {
                    "class_name": class_data.get('name'),
                    "method_name": method_data.get('name')
                    # "return_types": [rv.get("type") for rv in method_data.get("return_values", [])]
                }
                chunks.extend(self._split_text_with_metadata(
                    method_text,
                    method_metadata,
                    "method",
                    f"{class_data.get('name')}.{method_data.get('name')}"
                ))

            # Process attributes
            for attr_data in class_data.get("attributes", {}):
                attr_text = f"Attribute: {attr_data.get('name')} {'[Optional]' if attr_data.get('optional', False) else ''}\nRead_type: {attr_data.get('read_type')}\n{'Write_type: ' + (json.dumps(attr_data.get('write_type')) if isinstance(attr_data.get('write_type'), dict) else attr_data.get('write_type')) if attr_data.get('write_type') else ''}\nDescription: {attr_data.get('description', '')}\n{'Examples: ' + (json.dumps(attr_data.get('examples')) if isinstance(attr_data.get('examples'), (dict, list)) else str(attr_data.get('examples'))) if attr_data.get('examples') else ''}"
                attr_metadata = {
                    "class_name": class_data.get('name'),
                    "attribute_name": attr_data.get('name')
                    # "read_type": attr_data.get('complex_type'
                }
                chunks.extend(self._split_text_with_metadata(
                    attr_text,
                    attr_metadata,
                    "attribute",
                    f"{class_data.get('name')}.{attr_data.get('name')}"
                ))
            
            # Process operators
            for operator_data in class_data.get("operators", {}):
                operator_text = f"Operator: {operator_data.get('name')} {'[Optional]' if operator_data.get('optional', False) else ''}\nRead_type: {operator_data.get('read_type')}\n{'Write_type: ' + (json.dumps(operator_data.get('write_type')) if isinstance(operator_data.get('write_type'), dict) else operator_data.get('write_type')) if operator_data.get('write_type') else ''}\nDescription: {operator_data.get('description', '')}\n{'Examples: ' + (json.dumps(operator_data.get('examples')) if isinstance(operator_data.get('examples'), (dict, list)) else str(operator_data.get('examples'))) if operator_data.get('examples') else ''}"
                operator_metadata = {
                    "class_name": class_data.get('name'),
                    "operator_name": operator_data.get('name')
                }
                chunks.extend(self._split_text_with_metadata(
                    operator_text,
                    operator_metadata,
                    "operator",
                    f"{class_data.get('name')}.{operator_data.get('name')}"
                ))

        # Process events
        for event_data in api_json.get("events", {}):
            event_text = f"Event: {event_data.get('name')}\nDescription: {event_data.get('description', '')}\n{'Examples: ' + (json.dumps(event_data.get('examples')) if isinstance(event_data.get('examples'), (dict, list)) else str(event_data.get('examples'))) if event_data.get('examples') else ''}"
            event_metadata = {
                "event_name": event_data.get('name')
            }
            chunks.extend(self._split_text_with_metadata(
                event_text,
                event_metadata,
                "event",
                event_data.get('name')
            ))
            
            for data in event_data.get("data", {}):
                data_text = f"Data: {data.get('name')} {'[Optional]' if data.get('optional', False) else ''}\nType: {data.get('type')}\nDescription: {data.get('description', '')}\n"
                data_metadata = {
                    "event_name": event_data.get('name'),
                    "data_name": data.get('name'),
                    "data_type": data.get('type')
                }
                chunks.extend(self._split_text_with_metadata(
                    data_text,
                    data_metadata,
                    "data",
                    data.get('name')
                ))

        # Process concepts
        for concept_data in api_json.get("concepts", {}):
            concept_text = f"Concept: {concept_data.get('name')}\nDescription: {concept_data.get('description', '')}\nComplex_type: {concept_data.get('type','')}"
            
            concept_metadata = {
                "concept_name": concept_data.get('name'),
                "concept_type": concept_data.get('type').get('complex_type') if isinstance(concept_data.get('type'), dict) else concept_data.get('type')
            }
            chunks.extend(self._split_text_with_metadata(
                concept_text,
                concept_metadata,
                "concept",
                concept_data.get('name')
            ))

        # Process defines
        for define_data in api_json.get("defines", {}):
            define_text = f"Define: {define_data.get('name')}\nDescription: {define_data.get('description', '')}"
            define_metadata = {
                "define_name": define_data.get('name'),
                "define_type": define_data.get('type'),
            }
            chunks.extend(self._split_text_with_metadata(
                define_text,
                define_metadata,
                "define",
                define_data.get('name')
            ))
            
            for value_data in define_data.get("values", {}):
                value_text = f"Value: {value_data.get('name')}\nDescription: {value_data.get('description', '')}"
                value_metadata = {
                    "define_name": define_data.get('name'),
                    "value_name": value_data.get('name'),
                    "value_type": value_data.get('type'),
                }
                chunks.extend(self._split_text_with_metadata(
                    value_text,
                    value_metadata,
                    "value",
                    value_data.get('name')
                ))
        return chunks

    def _format_method_text(self, class_name: str, method_name: str, method_data: Dict) -> str:
        """Format method data into a text string."""
        text_parts = [
            f"Method: {class_name}.{method_name}",
            f"Description: {method_data.get('description', '')}"
        ]

        # Add parameters
        if method_data.get("parameters"):
            text_parts.append("\nParameters:")
            for param in method_data["parameters"]:
                text_parts.append(f"- {param['name']} ({param['type']}){'[Optional]' if param['optional'] else ''}: {param['description']}")

        # Add return values
        if method_data.get("return_values"):
            text_parts.append("\nReturns:")
            for rv in method_data["return_values"]:
                text_parts.append(f"- {rv['type']}: {rv['description']}")

        # Add raises events
        if method_data.get("raises"):
            text_parts.append("\nRaises:")
            for raise_data in method_data["raises"]:
                text_parts.append(f"- {raise_data['name']}: {raise_data['description']}")

        # Add examples
        if method_data.get("examples"):
            text_parts.append("\nExamples:")
            text_parts.extend(method_data["examples"])

        # Add format
        if method_data.get("format"):
            text_parts.append("\nFormat:")
            text_parts.append(f"- {method_data['format']}")

        # Add variant parameter groups
        if method_data.get("variant_parameter_groups"):
            text_parts.append("\nVariant Parameter Groups:")
            for variant_group in method_data["variant_parameter_groups"]:
                text_parts.append(f"- {variant_group['name']}: {variant_group['description']}")
                if variant_group.get("parameters") and len(variant_group["parameters"]) > 0:
                    for param in variant_group["parameters"]:
                        text_parts.append(f"- {param['name']} ({param['type']}){'[Optional]' if param['optional'] else ''}: {param['description']}")

        return "\n".join(text_parts)

    def process_wiki_doc(self, wiki_json: Dict) -> List[Dict]:
        """Process wiki document"""
        chunks = []
        for wiki_data in wiki_json:
            wiki_chunks = self.long_text_splitter.split_text(wiki_data.get("content"))
            for i, chunk in enumerate(wiki_chunks):
                chunks.append({
                    "type": "wiki",
                    "name": wiki_data.get("title"),
                    # "name": wiki_data.get("title") + f"-{i+1}",
                    "content": chunk,
                })
        return chunks

def main():
    # Define paths
    # input_file = os.path.join("data", "raw", "runtime-api.json")
    wiki_file = os.path.join("data", "raw", "wiki_pages.json")
    output_file = os.path.join("data", "processed", "chunks", "wiki_chunks.json")

    # # Load API documentation
    # with open(input_file, 'r', encoding='utf-8') as f:
    #     api_json = json.load(f)

    with open(wiki_file, 'r', encoding='utf-8') as f:
        wiki_json = json.load(f)

    # Process documentation
    processor = DocProcessor(chunk_size=256, chunk_overlap=64)
    # api_chunks = processor.process_api_doc(api_json)
    wiki_chunks = processor.process_wiki_doc(wiki_json)
    # chunks = api_chunks + wiki_chunks

    # Save chunks
    print(f"Saving chunks to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(wiki_chunks, f, indent=2, ensure_ascii=False)

    print("Done!")

if __name__ == "__main__":
    main()