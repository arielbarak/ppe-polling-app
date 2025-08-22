import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, Space, message } from 'antd';
import { SendOutlined, HomeOutlined } from '@ant-design/icons';
import { pollApi } from '../api/pollApi';

const { Title } = Typography;
const { TextArea } = Input;

function CreatePoll({ navigateToPoll, navigateToHome }) {
  const [form] = Form.useForm();
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (values) => {
    setIsLoading(true);
    
    // Split the options text area by new lines and filter out empty lines
    const optionsArray = values.options.split('\n').filter(opt => opt.trim() !== '');

    if (optionsArray.length < 2) {
      message.error('Please provide at least two options on separate lines.');
      setIsLoading(false);
      return;
    }

    try {
      const newPoll = await pollApi.createPoll({ 
        question: values.question, 
        options: optionsArray 
      });
      message.success('Poll created successfully!');
      navigateToPoll(newPoll.id);
    } catch (err) {
      message.error(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%', maxWidth: 600, margin: '0 auto' }}>
      <Card>
        <Title level={2} style={{ textAlign: 'center' }}>Create a New Poll</Title>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          style={{ maxWidth: '100%' }}
        >
          <Form.Item
            label="Poll Question"
            name="question"
            rules={[
              { required: true, message: 'Please enter your poll question' }
            ]}
          >
            <Input
              placeholder="e.g., What is your favorite color?"
              size="large"
            />
          </Form.Item>

          <Form.Item
            label="Options (one per line)"
            name="options"
            rules={[
              { required: true, message: 'Please enter at least two options' }
            ]}
            style={{ marginBottom: '20px' }}          >
            <TextArea
              placeholder="e.g.,
Red
Green
Blue"
              rows={4}
              size="large"
            />
          </Form.Item>

          <Form.Item style={{ textAlign: 'center', marginTop: '12px' }}> 
            <Space direction="vertical" size="middle">
              <Button
                type="primary"
                htmlType="submit"
                loading={isLoading}
                icon={<SendOutlined />}
                size="large"
              >
                {isLoading ? 'Creating...' : 'Create Poll'}
              </Button>
              
              <Button 
                icon={<HomeOutlined />}
                onClick={navigateToHome}
              >
                Back to Home
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </Space>
  );
}

export default CreatePoll;
