import { Story } from "@storybook/react";
import axios from "axios";
import MockAdapter from "axios-mock-adapter";
import React from "react";
import Main from "../Main";

const axiosMock = new MockAdapter(axios);

export default {
  title: "Main",
  component: Main,
  parameters: {
    layout: "fullscreen",
  },
};

const Template: Story = (_args) => {
  axiosMock.onGet("print_status").reply(200, {
    selected_file: "lattice.ctb",
    is_printing: true,
    progress: 25.0,
  });
  return <Main />;
};

export const Default = Template.bind({});
