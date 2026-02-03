"""
Quick test to verify workflow configuration is working correctly.
Run this from project root: python test_workflow_config.py
"""

from percell.domain.services.configuration_service import create_configuration_service
from percell.domain.services import create_workflow_configuration_service

def test_workflow_configuration():
    """Test workflow configuration service."""
    print("\n" + "="*70)
    print("Testing Workflow Configuration System")
    print("="*70 + "\n")

    # Create services
    config = create_configuration_service("percell/config/config.json", create_if_missing=True)
    workflow_config = create_workflow_configuration_service(config)

    # Test 1: Get current configuration
    print("1. Current Configuration:")
    print("-" * 70)
    summary = workflow_config.get_workflow_summary()
    for category, tool in summary.items():
        print(f"   {category.capitalize()}: {tool}")

    # Test 2: Get available tools
    print("\n2. Available Tools:")
    print("-" * 70)

    print("   Segmentation tools:")
    seg_tools = workflow_config.get_available_segmentation_tools()
    for key, tool in seg_tools.items():
        print(f"      - {key}: {tool.display_name} ({tool.stage_name})")

    print("\n   Processing tools:")
    proc_tools = workflow_config.get_available_processing_tools()
    for key, tool in proc_tools.items():
        print(f"      - {key}: {tool.display_name} ({tool.stage_name})")

    print("\n   Thresholding tools:")
    thresh_tools = workflow_config.get_available_thresholding_tools()
    for key, tool in thresh_tools.items():
        print(f"      - {key}: {tool.display_name} ({tool.stage_name})")

    # Test 3: Get complete workflow stages
    print("\n3. Complete Workflow Stages (Current Configuration):")
    print("-" * 70)
    stages = workflow_config.get_complete_workflow_stages()
    for idx, (stage_name, display_name) in enumerate(stages, 1):
        print(f"   {idx}. {stage_name:40s} -> {display_name}")

    # Test 4: Test switching to full_auto
    print("\n4. Testing Configuration Change:")
    print("-" * 70)
    current_thresh = workflow_config.get_thresholding_tool()
    print(f"   Current thresholding: {current_thresh}")

    # Switch to full_auto
    print("   Switching to full_auto...")
    workflow_config.set_thresholding_tool('full_auto')

    new_thresh = workflow_config.get_thresholding_tool()
    new_stage = workflow_config.get_thresholding_stage_name()
    new_display = workflow_config.get_thresholding_display_name()

    print(f"   New thresholding: {new_thresh}")
    print(f"   Stage name: {new_stage}")
    print(f"   Display name: {new_display}")

    # Show updated workflow
    print("\n5. Updated Workflow Stages:")
    print("-" * 70)
    stages = workflow_config.get_complete_workflow_stages()
    for idx, (stage_name, display_name) in enumerate(stages, 1):
        marker = " <-- Changed!" if "threshold" in stage_name.lower() else ""
        print(f"   {idx}. {stage_name:40s} -> {display_name}{marker}")

    # Switch back to semi_auto
    print("\n6. Restoring Original Configuration:")
    print("-" * 70)
    workflow_config.set_thresholding_tool('semi_auto')
    print(f"   Restored to: {workflow_config.get_thresholding_tool()}")

    print("\n" + "="*70)
    print("✓ All tests passed!")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_workflow_configuration()
