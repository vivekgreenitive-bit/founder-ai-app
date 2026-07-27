class ResponseComposer:
    def run(self, framework_name: str, strategy: dict, execution: dict) -> str:
        # Reassemble exactly into the expected 7-part output template
        template = f"""## 1. Business Scenario
{strategy.get('scenario', '')}

## 2. Framework Name
{framework_name}

## 3. Applied Sections
{strategy.get('applied_sections', '')}

## 4. Priority Action
{execution.get('priority_action', '')}

## 5. Dreamer
{strategy.get('dreamer', '')}

## 6. Guardian
{strategy.get('guardian', '')}

## 7. Athlete
{execution.get('athlete', '')}"""
        return template
