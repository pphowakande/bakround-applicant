import React from 'react';
import Dialog from 'material-ui/Dialog';
import FlatButton from 'material-ui/FlatButton';
import RaisedButton from 'material-ui/RaisedButton';
import { confirmable } from 'react-confirm';
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';

class Confirmation extends React.Component {
  render() {
    const {
      okLabel = 'Yes',
      cancelLabel = 'No',
      title,
      confirmation,
      show,
      proceed,
      dismiss,
      cancel,
      modal,
    } = this.props;

    const actions = [
      <FlatButton
        label={cancelLabel}
        primary={true}
        onTouchTap={cancel}
      />,
      <FlatButton
        label={okLabel}
        primary={true}
        keyboardFocused={true}
        onTouchTap={proceed}
      />,
    ];

    return ( <MuiThemeProvider>
        <Dialog
          title={title}
          actions={actions}
          modal={modal}
          open={show}
          onRequestClose={dismiss}
        >
          {confirmation}
        </Dialog>
      </MuiThemeProvider>
    );
  }
}

export default confirmable(Confirmation);