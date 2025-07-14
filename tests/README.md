# ICUConnect Testing Results & Analysis

This document demonstrates the functionality, robustness, and performance of the ICUConnect system under a variety of testing strategies, data values, and hardware/software environments. It is structured to provide, for each test file: a description, a screenshot of results (where available), and an analysis of what the results mean. Recommendations and future work are provided at the end.

---

## 1. Testing Strategies

We employ four main testing strategies:

- **Unit Tests**
- **Integration Tests**
- **Functional Tests**
- **Performance & Load Tests**

---

## 2. Test Files, Results, and Analysis

### 2.1. Unit Tests (`test_models.py`)

**Description:**

The unit tests in `test_models.py` provide a thorough examination of all the core data models and business logic within the ICUConnect system. The tests begin by validating the creation of hospitals, ensuring that each hospital is assigned a unique name, verification code, and timezone, and that its notification duration is set correctly. The properties of each hospital, such as the total and available beds, are checked to confirm that they are always non-negative and that the number of available beds never exceeds the total.

User creation is tested by generating users with unique emails, names, and employee IDs, and by verifying that passwords are securely hashed and validated. The format of user IDs is also checked to ensure consistency across the system. User settings are tested both with custom values and with default values, confirming that notification durations, audio and visual notification preferences, and other settings are correctly stored and retrieved.

The Bed model is tested for both creation and uniqueness. The tests ensure that each bed has a unique number within its hospital and that attempts to create duplicate beds are properly rejected by the database. Referral requests are created between hospitals for patients of varying ages and genders, and the tests verify that referrals are initialized with the correct status and urgency. The time since referral creation and the escalation logic are also validated, including scenarios where an old referral should trigger an escalation due to elapsed time.

Patient transfers are tested by creating transfers for referrals and checking that all patient and transfer details are correctly recorded. The tests also examine the time properties of transfers, such as the time since a transfer was set to 'En Route' and the calculation of transfer duration, ensuring that these values are accurate depending on the transfer's status.

Admissions are tested by admitting patients to beds and verifying that the admission status is set to 'Active', that patient information is correctly masked or initialized, and that the length of stay is calculated appropriately. The tests also confirm that discharge times are only set for completed admissions.

For the Admin model, the tests cover the creation of admins with different privilege levels, the correct hashing and validation of admin passwords, and the toggling of verification status. The format of admin IDs is checked, and the distinction between hospital and super admins is validated.

Finally, the Discharge model is tested by creating discharge records for patients, ensuring that all relevant information, such as discharge type and notes, is saved and retrievable. The tests also check the calculation of patient initials and the correct handling of different discharge types, as well as the validation of local admission and discharge times and the length of stay.

**Screenshot:**

- ![Unit Test Screenshot](images/unit%20test.png)

**Analysis:**

- These tests cover a wide range of scenarios, including normal operations, edge cases (e.g., duplicate beds, old referrals), and validation of computed properties.
- By using dynamic and varied data values, the tests ensure the models are robust and behave correctly under different conditions.
- All tests passed meaning that each of the features are functioning well.

**How to Run Unit Tests:**

To run the unit tests, simply execute:

```bash
pytest tests/test_models.py
```

---

### 2.2. Intergration Tests (`test_api.py`)

**Description:**

The integration tests are designed to verify that the different components of the ICUConnect system work together seamlessly. These tests simulate real-world API usage by interacting with the authentication, referral, transfer, admission, and user settings endpoints. The authentication tests ensure that users can log in with valid credentials and are prevented from logging in with incorrect ones. The referral workflow is tested, including the initiation of new referrals, fetching pending referrals, responding to referrals (such as accepting or rejecting them), and escalating referrals when necessary.

Transfers are tested by simulating the creation of patient transfers based on accepted referrals, updating transfer statuses, and retrieving lists of active transfers. The admissions API is tested by admitting patients, querying available beds, and ensuring that all relevant admission data is handled correctly.

User settings endpoints are exercised to confirm that users can retrieve and update their notification and escalation preferences. Additionally, the integration tests include error handling scenarios, such as submitting invalid JSON, omitting required fields, and attempting unauthorized access to protected endpoints. By using a variety of data values and simulating different user roles and workflows, these tests ensure that the backend logic is robust, that data flows correctly between components, and that the system responds appropriately to both valid and invalid requests.

**Recent Improvements & Error Handling:**

During the development and refinement of these integration tests, several issues were encountered and systematically addressed:

- **Test Data Isolation & Robustness:**

  - Early test failures were caused by missing or misconfigured test data (e.g., hospitals without beds, referrals in the wrong state, or users not verified/approved).
  - The test fixture was updated to dynamically create multiple hospitals, users (for each hospital), and beds, ensuring all required relationships and states are present for every test scenario.
  - A third hospital was added to support escalation logic, and all relevant IDs are now stored in the app config for dynamic use in tests.

- **API Error Handling:**

  - Several endpoints were updated to handle invalid JSON, missing fields, and permission errors gracefully, always returning a consistent JSON structure with a `success` key and clear error messages.
  - The escalation endpoint was refactored to use a dynamic hospital ID (from the test config) for escalations, rather than a hardcoded value, ensuring tests can control escalation targets.

- **Test Logic Updates:**

  - Tests were updated to log in as the correct user for each action (e.g., responding to a referral as the target hospital's doctor).
  - Tests that require a referral or transfer in a specific state now set up that state within the test, rather than relying on the fixture alone.

**Screenshot:**

- ![Intergration Test Screenshot](images/int%20test.png)

- **Result:**
  - These changes resulted in a fully passing integration test suite, with robust coverage of both normal and edge-case workflows, and reliable, repeatable test runs.

**How to Run Integration Tests:**

To run the integration tests, make sure your test database and environment are set up, then run:

```bash
pytest tests/test_api.py -v
```

---

### 2.3. Functional Tests (`test_functional.py`)

**Description:**

The functional tests use Selenium WebDriver to automate real browser interactions with the ICUConnect web application. These tests simulate real user workflows, such as logging in, managing users, creating referrals, responding to referrals, admitting patients, and monitoring patient status. The tests cover workflows for hospital admins, doctors, and nurses, as well as cross-hospital scenarios and real-time updates.

**Recent Improvements:**

- The functional test suite was expanded to cover more user roles and workflows, including cross-hospital referrals and real-time dashboard updates.
- Test data setup was improved to ensure all required users, hospitals, and beds exist for each workflow.
- Tests now run in headless mode for CI compatibility and faster execution.

**How to Run Functional Tests:**

To run the functional tests, you need Chrome and the ChromeDriver installed. Make sure your Flask app is running locally (default: http://localhost:5000) before running the tests.

```bash
pytest tests/test_functional.py -v
```

You can also specify a different browser or run a subset of tests using pytest options.

**Analysis:**

- These tests ensure that the user interface and backend work together as expected in real-world scenarios.
- By automating browser actions, they catch issues that unit and integration tests may miss, such as JavaScript errors, UI regressions, and workflow problems.
- The suite provides confidence that the system is usable and robust from an end-user perspective.

---

### 2.4. Performance Tests (`test_performance.py`)

**Description:**

The performance tests in `test_performance.py` provide a comprehensive evaluation of the ICUConnect system's scalability, efficiency, and robustness under high load and concurrent usage. These tests are designed to simulate real-world stress scenarios, including bulk data operations, concurrent user activity, and error recovery, ensuring the system can handle demanding production environments.

**What is Tested:**

The performance test suite covers three main categories:

1. **Basic Performance Tests** (`TestPerformance` class):

   - **Referral Creation Performance**: Creates 100 referrals with batched commits (20 per batch) - **time limit: 30 seconds**
   - **Concurrent Referral Creation**: Creates 50 referrals using 10 concurrent threads - **time limit: 60 seconds**
   - **Database Query Performance**: Creates 1,000 referrals, then tests query performance - **time limit: 15 seconds for full query, 5 seconds for filtered query**
   - **Memory Usage**: Monitors memory consumption during operations - **limit: < 100MB increase**
   - **Notification Duration Calculation**: Tests time calculations for 100 referrals - **time limit: 10 seconds**
   - **Transfer Status Updates**: Updates 100 transfer statuses in batches - **time limit: 120 seconds**
   - **Escalation Logic Performance**: Tests escalation logic on 100 referrals - **time limit: 10 seconds**
   - **Error Recovery**: Tests system recovery from errors with 100 iterations - **time limit: 30 seconds**

2. **Load Testing** (`TestLoadTesting` class):

   - **High Concurrent Users**: Simulates 20 concurrent users performing 10 operations each - **time limit: 30 seconds**
   - **Database Connection Pool**: Tests 15 concurrent database operations - **time limit: 20 seconds**

3. **Stress Testing** (`TestStressTesting` class):
   - **Large Dataset Performance**: Creates 500 referrals and performs complex queries - **time limit: 60 seconds total, 10 seconds for queries**
   - **Error Recovery**: Tests error recovery with 100 operations - **time limit: 30 seconds**

**Recent Improvements:**

The performance tests initially faced several challenges that were systematically resolved:

- **Memory Management**: Tests were added to ensure memory usage stays under 100MB during operations, preventing memory leaks in production.

- **Batch Processing**: Referral creation was optimized using batch commits (20-50 records per commit) to improve performance from individual commits.

- **Thread Safety**: Each concurrent operation now uses its own SQLAlchemy session and engine, with proper cleanup in `finally` blocks to prevent resource leaks.

- **Realistic Delays**: Added small delays (`time.sleep(0.01)`) in user simulation to mimic real user behavior patterns.

**How to Run:**

```bash
# Run all performance tests
pytest tests/test_performance.py -v
```

**Screenshot:**

- ![Performance Test Screenshot](images/perf%20test.png)

**Analysis:**

The performance test results demonstrate that the ICUConnect system can handle:

- **Bulk Operations**: Creating 100-500 referrals efficiently with batched commits
- **Concurrent Access**: Supporting 10-20 concurrent users without performance degradation
- **Large Datasets**: Querying 1,000+ records within acceptable time limits
- **Memory Efficiency**: Maintaining stable memory usage under load
- **Error Resilience**: Recovering gracefully from database errors and continuing operations

All tests complete within their specified time limits, indicating the system is ready for production deployment with proper monitoring and scaling strategies in place.

---
